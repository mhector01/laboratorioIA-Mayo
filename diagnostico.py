import cv2
import time

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer.yml')

usuarios = {1: "Héctor", 2: "Prueba"}

cap = cv2.VideoCapture(0)
time.sleep(2)

print("=== DIAGNÓSTICO LBPH ===")
print("Presiona 'q' para salir\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rostros = face_cascade.detectMultiScale(gris, 1.3, 5)

    for (x, y, w, h) in rostros:
        roi = gris[y:y+h, x:x+w]
        id_user, error = recognizer.predict(roi)
        confianza = round(100 - error, 2)

        nombre = usuarios.get(id_user, f"ID_{id_user}_no_en_dict")
        print(f"  → ID={id_user} | LBPH_score={error:.2f} | confianza={confianza}% | nombre={nombre}")
        print(f"    Umbral actual: 70  →  {'RECONOCIDO' if error < 70 else 'DESCONOCIDO'}")

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, f"ID={id_user} score={error:.1f}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow('Diagnostico LBPH', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
