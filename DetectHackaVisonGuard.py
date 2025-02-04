import os
import cv2
import threading
import smtplib
import mimetypes
from datetime import datetime
from ultralytics import YOLO
from email.message import EmailMessage
import tkinter as tk
from tkinter import filedialog
import time

# Configuração do e-mail
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "securytevisionguard@gmail.com"  
EMAIL_PASSWORD = "qihv lyhu ajng gncr"  
EMAIL_RECEIVER = "jordanmam29@gmail.com" 

# Variável global para controle da execução
running = False
cap = None  
alert_sent = False  # Garante que o e-mail seja enviado apenas uma vez

# Lock para sincronizar as threads
lock = threading.Lock()

# Função para enviar o e-mail com a imagem
def send_email(image_path):
    msg = EmailMessage()
    msg["Subject"] = "⚠️ Alerta de Objeto Perigoso Detectado!"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content("Um objeto perigoso foi detectado pela câmera. A imagem está anexada.")

    # Anexar a imagem
    ctype, encoding = mimetypes.guess_type(image_path)
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"

    maintype, subtype = ctype.split("/", 1)
    with open(image_path, "rb") as img:
        msg.add_attachment(img.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(image_path))

    # Enviar o e-mail
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"E-mail enviado para {EMAIL_RECEIVER} com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# Função de detecção em thread separada
def detect_objects(video_source=0):
    global running, cap, alert_sent
    running = True  
    model = YOLO('runs/detect/train/weights/best.pt')  
    cap = cv2.VideoCapture(video_source)

    captured_images_dir = "captured_images"
    os.makedirs(captured_images_dir, exist_ok=True)

    while cap.isOpened():
        if not running:
            break  

        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].numpy()
                confidence = box.conf[0]
                cls = box.cls[0]

                if confidence > 0.6:
                    label = f"{model.names[int(cls)]} {confidence:.2f}"
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                    cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                    if model.names[int(cls)] in ['pistol', 'knife'] and not alert_sent:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_path = os.path.join(captured_images_dir, f"suspect_{timestamp}.jpg")
                        
                        # Sincronizar a gravação da imagem com o lock
                        with lock:
                            cv2.imwrite(image_path, frame)
                            print(f"Imagem salva: {image_path}")
                            
                            # Enviar o e-mail apenas uma vez
                            threading.Thread(target=send_email, args=(image_path,)).start()
                            alert_sent = True  # Marca que o e-mail já foi enviado

        # Exibir o frame
        cv2.imshow('Detection', frame)

        # Verificar se o usuário pressionou 'q' para sair
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q') or key == 27:  
            running = False
            break

    stop_detection()

# Função para liberar recursos corretamente
def stop_detection():
    global cap, running
    running = False
    if cap:
        cap.release()
        cap = None
    cv2.destroyAllWindows()

# Interface gráfica com Tkinter
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("VisionGuard - Detecção de Objetos Cortantes")
        self.root.geometry("400x200")

        self.label = tk.Label(root, text="Selecione a fonte de vídeo:", font=("Arial", 14))
        self.label.pack(pady=20)

        self.camera_button = tk.Button(root, text="Câmera", command=self.start_camera, width=20)
        self.camera_button.pack(pady=10)

        self.video_button = tk.Button(root, text="Vídeo", command=self.open_video, width=20)
        self.video_button.pack(pady=10)

        self.quit_button = tk.Button(root, text="Fechar", command=self.quit_app, width=20)
        self.quit_button.pack(pady=10)

        self.thread = None  

    def start_camera(self):
        global running
        if not running:
            self.thread = threading.Thread(target=detect_objects, args=(0,), daemon=True)
            self.thread.start()

    def open_video(self):
        global running
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi")])
        if file_path and not running:
            self.thread = threading.Thread(target=detect_objects, args=(file_path,), daemon=True)
            self.thread.start()

    def quit_app(self):
        stop_detection()  # Libera câmera e janelas do OpenCV
        self.root.quit()
        self.root.destroy()

# Executar a aplicação
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)  
    root.mainloop()