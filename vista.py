from flask import Flask, render_template, Response
import cv2
# Importar aquí tu clase corregida del SmartGate

app = Flask(__name__)

def generar_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success: break
        
        # AQUÍ VA TU LÓGICA DE IA (HAAR CASCADES + LBPH)
        # frame_procesado = smart_gate.procesar(frame)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    # Este archivo index.html es el que generamos con la IA
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)