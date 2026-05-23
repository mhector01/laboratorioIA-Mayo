import json
import time
from datetime import datetime

import cv2
from flask import Flask, render_template, Response, jsonify, request

from camera import CameraStream
from database import init_db
from smart_gate import SmartGate

app = Flask(__name__)

init_db()
gate = SmartGate.get_instance()
camera = CameraStream.get_instance()

ESTADO_MAP = {
    "acceso": "Normal",
    "anomalia": "Anomalía: Viaje Imposible",
    "desconocido": "Intruso"
}


def generar_frames():
    while True:
        ret, frame = camera.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        frame_procesado = gate.procesar(frame, camera_read=camera.read)

        ret, buffer = cv2.imencode('.jpg', frame_procesado)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'
               + buffer.tobytes() + b'\r\n')


def row_to_dict_log(row):
    timestamp = row["timestamp"]
    estado = ESTADO_MAP.get(row["tipo_evento"], row["tipo_evento"])
    return {
        "id": row["id_evento"],
        "usuario": row["usuario"] or "Desconocido",
        "ubicacion": row["ubicacion"] or "N/A",
        "confianza": row["confianza"] or 0,
        "estado": estado,
        "fecha": datetime.fromtimestamp(timestamp).strftime(
            "%d-%m-%Y %H:%M:%S"
        )
    }


def row_to_dict_evento(row):
    snapshots_raw = row["snapshots"]
    try:
        snapshots = json.loads(snapshots_raw) if snapshots_raw else []
    except (json.JSONDecodeError, TypeError):
        snapshots = []
    return {
        "id_evento": row["id_evento"],
        "timestamp": row["timestamp"],
        "usuario": row["usuario"],
        "ubicacion": row["ubicacion"],
        "confianza": row["confianza"],
        "tipo_evento": row["tipo_evento"],
        "accion_tomada": row["accion_tomada"],
        "snapshots": snapshots,
        "fecha": datetime.fromtimestamp(
            row["timestamp"]
        ).strftime("%d-%m-%Y %H:%M:%S")
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(
        generar_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/api/logs')
def api_logs():
    gate.cursor.execute("""
        SELECT *
        FROM eventos_acceso
        ORDER BY id_evento DESC
        LIMIT 10
    """)
    rows = gate.cursor.fetchall()
    return jsonify([row_to_dict_log(r) for r in rows])


@app.route('/api/eventos')
def api_eventos():
    limite = request.args.get("limite", 50, type=int)
    gate.cursor.execute("""
        SELECT *
        FROM eventos_acceso
        ORDER BY id_evento DESC
        LIMIT ?
    """, (limite,))
    rows = gate.cursor.fetchall()
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "data": [row_to_dict_evento(r) for r in rows]
    })


@app.route('/api/eventos/hoy')
def api_eventos_hoy():
    hace_24h = time.time() - 86400
    gate.cursor.execute("""
        SELECT *
        FROM eventos_acceso
        WHERE timestamp > ?
        ORDER BY id_evento DESC
    """, (hace_24h,))
    rows = gate.cursor.fetchall()
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "data": [row_to_dict_evento(r) for r in rows]
    })


@app.route('/api/estadisticas')
def api_estadisticas():
    gate.cursor.execute("""
        SELECT tipo_evento, accion_tomada, COUNT(*) as total
        FROM eventos_acceso
        GROUP BY tipo_evento, accion_tomada
    """)
    rows = gate.cursor.fetchall()
    conteo = [dict(r) for r in rows]
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "data": conteo
    })


@app.route('/api/cooldown', methods=['POST'])
def api_set_cooldown():
    data = request.get_json(silent=True)
    if not data or "segundos" not in data:
        return jsonify({
            "status": "error",
            "mensaje": "Campo 'segundos' requerido"
        }), 400
    segundos = float(data["segundos"])
    if segundos < 0:
        return jsonify({
            "status": "error",
            "mensaje": "'segundos' debe ser >= 0"
        }), 400
    gate.cooldown_segundos = segundos
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "data": {"cooldown_segundos": segundos}
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
