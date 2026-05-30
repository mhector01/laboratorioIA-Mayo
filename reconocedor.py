from flask import Flask, render_template, Response, jsonify
import cv2
import sqlite3
import time
from datetime import datetime

app = Flask(__name__)

class SmartGate:
    def __init__(self):
        # ==============================
        # CONFIGURACIÓN DE CÁMARA
        # ==============================
        self.cap = cv2.VideoCapture(0)
        time.sleep(2.0)

        # ==============================
        # CLASIFICADOR HAAR CASCADE
        # ==============================
        self.face_cascade = cv2.CascadeClassifier(
            'haarcascade_frontalface_default.xml'
        )

        # ==============================
        # RECONOCEDOR LBPH
        # ==============================
        self.reconocedor = cv2.face.LBPHFaceRecognizer_create()
        self.reconocedor.read('trainer.yml')

        # ==============================
        # BASE DE DATOS SQLITE
        # ==============================
        self.conn = sqlite3.connect(
            'smart_gate.db',
            check_same_thread=False
        )

        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS eventos_acceso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,
                ubicacion TEXT,
                score_confianza REAL,
                estado TEXT,
                timestamp REAL,
                fecha TEXT
            )
        """)

        self.conn.commit()

        # ==============================
        # USUARIOS REGISTRADOS
        # ==============================
        self.usuarios = {
            1: "Héctor",
            2: "Prueba"
        }

        # ==============================
        # CONTROL DE REGISTRO
        # ==============================
        self.ultimo_registro = {}
        self.cooldown = 10

        # ==============================
        # UBICACIÓN ACTUAL
        # ==============================
        self.ubicacion_actual = "Puerta Principal"

    # ======================================================
    # REGISTRAR EVENTO EN BASE DE DATOS
    # ======================================================
    def registrar_evento(self, usuario, ubicacion, confianza, estado):
        timestamp_actual = time.time()

        fecha = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        self.cursor.execute("""
            INSERT INTO eventos_acceso
            (usuario, ubicacion, score_confianza, estado, timestamp, fecha)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            usuario,
            ubicacion,
            confianza,
            estado,
            timestamp_actual,
            fecha
        ))

        self.conn.commit()

        print(f"[{estado}] {usuario} | {ubicacion}")

    # ======================================================
    # VALIDAR ANOMALÍA TEMPORAL
    # ======================================================
    def detectar_anomalia(self, usuario, ubicacion_actual):
        self.cursor.execute("""
            SELECT ubicacion, timestamp
            FROM eventos_acceso
            WHERE usuario = ?
            ORDER BY id DESC
            LIMIT 1
        """, (usuario,))

        ultimo = self.cursor.fetchone()

        if ultimo:
            ultima_ubicacion, ultimo_timestamp = ultimo

            diferencia = time.time() - ultimo_timestamp

            if (
                ultima_ubicacion != ubicacion_actual
                and diferencia < 15
            ):
                return True

        return False

    # ======================================================
    # GENERADOR DE FRAMES PARA FLASK
    # ======================================================
    def generar_frames(self):

        while True:

            ret, frame = self.cap.read()

            if not ret:
                continue

            frame = cv2.flip(frame, 1)

            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            rostros = self.face_cascade.detectMultiScale(
                gris,
                scaleFactor=1.3,
                minNeighbors=5
            )

            for (x, y, w, h) in rostros:

                roi_gris = gris[y:y+h, x:x+w]

                id_user, error = self.reconocedor.predict(roi_gris)

                confianza = round(100 - error, 2)

                # =====================================
                # VALIDACIÓN DE IDENTIDAD
                # =====================================
                if error < 70:

                    usuario = self.usuarios.get(
                        id_user,
                        "Desconocido"
                    )

                    color = (0, 255, 0)

                    estado = "Normal"

                    # =====================================
                    # DETECCIÓN DE ANOMALÍA
                    # =====================================
                    anomalia = self.detectar_anomalia(
                        usuario,
                        self.ubicacion_actual
                    )

                    if anomalia:
                        estado = "Anomalía: Viaje Imposible"
                        color = (0, 0, 255)

                else:

                    usuario = "Desconocido"
                    estado = "Intruso"
                    color = (0, 0, 255)

                # =====================================
                # COOLDOWN POR USUARIO
                # =====================================
                ahora = time.time()

                ultimo = self.ultimo_registro.get(usuario, 0)

                if ahora - ultimo > self.cooldown:

                    self.registrar_evento(
                        usuario=usuario,
                        ubicacion=self.ubicacion_actual,
                        confianza=confianza,
                        estado=estado
                    )

                    self.ultimo_registro[usuario] = ahora

                # =====================================
                # DIBUJAR INTERFAZ EN FRAME
                # =====================================
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    color,
                    2
                )

                texto = f"{usuario} | {estado}"

                cv2.putText(
                    frame,
                    texto,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

            # =====================================
            # CONVERTIR FRAME A JPEG
            # =====================================
            ret, buffer = cv2.imencode('.jpg', frame)

            frame_bytes = buffer.tobytes()

            # =====================================
            # STREAMING HTTP
            # =====================================
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )

# ==========================================
# INSTANCIA GLOBAL
# ==========================================
gate = SmartGate()

# ==========================================
# RUTA PRINCIPAL
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# STREAM DE VIDEO
# ==========================================
@app.route('/video_feed')
def video_feed():

    return Response(
        gate.generar_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# ==========================================
# API DE LOGS EN TIEMPO REAL
# ==========================================
@app.route('/api/logs')
def api_logs():

    gate.cursor.execute("""
        SELECT
            id,
            usuario,
            ubicacion,
            score_confianza,
            estado,
            fecha
        FROM eventos_acceso
        ORDER BY id DESC
        LIMIT 10
    """)

    rows = gate.cursor.fetchall()

    logs = []

    for row in rows:
        logs.append({
            "id": row[0],
            "usuario": row[1],
            "ubicacion": row[2],
            "confianza": row[3],
            "estado": row[4],
            "fecha": row[5]
        })

    return jsonify(logs)

# ==========================================
# EJECUTAR SERVIDOR
# ==========================================
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )