import os
import cv2
import threading
import smtplib
import mimetypes
import face_recognition
from datetime import datetime, timedelta
from ultralytics import YOLO
from email.message import EmailMessage
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np

# -------------------------------
# Configuração do e-mail
# -------------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "securytevisionguard@gmail.com"  # Substitua pelo seu e-mail
EMAIL_PASSWORD = "qihv lyhu ajng gncr"           # Substitua pela senha de aplicativo do Gmail
EMAIL_RECEIVER = "jordanmam29@gmail.com"

# -------------------------------
# Configurações e variáveis globais
# -------------------------------
running = False
cap = None

detected_faces_dir = "detected_faces"
os.makedirs(detected_faces_dir, exist_ok=True)
captured_images_dir = "captured_images"
os.makedirs(captured_images_dir, exist_ok=True)

lock = threading.Lock()

# Cache para armazenar os encodings dos rostos já salvos (útil para ambos os modos)
known_face_encodings = []
# Dicionário para o modo ao vivo: mapeia o índice do rosto (no cache) para o último horário (datetime)
# em que o alerta foi enviado (para não enviar alertas repetidos em intervalos menores que 30 min)
face_last_alert = {}

# -------------------------------
# Funções Auxiliares
# -------------------------------
def load_known_faces():
    """Carrega os rostos já salvos no cache a partir da pasta detected_faces."""
    global known_face_encodings
    for file in os.listdir(detected_faces_dir):
        image_path = os.path.join(detected_faces_dir, file)
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_face_encodings.append(encodings[0])
    print(f"{len(known_face_encodings)} rostos conhecidos carregados.")

def send_email(image_path, message="⚠️ Alerta!"):
    """Envia um e-mail com o alerta e a imagem capturada."""
    msg = EmailMessage()
    msg["Subject"] = message
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content("Foram registradas as seguintes detecções:\n" + message)
    
    ctype, encoding = mimetypes.guess_type(image_path)
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"
    maintype, subtype = ctype.split("/", 1)
    with open(image_path, "rb") as img:
        msg.add_attachment(img.read(), maintype=maintype, subtype=subtype,
                           filename=os.path.basename(image_path))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"E-mail enviado para {EMAIL_RECEIVER} com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def get_known_face_index(face_encoding):
    """Retorna o índice do rosto no cache se já estiver salvo; caso contrário, retorna None."""
    for i, known_encoding in enumerate(known_face_encodings):
        match = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.5)
        if match[0]:
            return i
    return None

def save_face(frame, face_location):
    """
    Salva a face detectada (caso seja nova) na pasta detected_faces e
    atualiza o cache. Retorna o índice do rosto no cache.
    """
    face_encodings = face_recognition.face_encodings(frame, known_face_locations=[face_location])
    if face_encodings:
        encoding = face_encodings[0]
        known_index = get_known_face_index(encoding)
        if known_index is None:
            top, right, bottom, left = face_location
            face_image = frame[top:bottom, left:right]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            face_path = os.path.join(detected_faces_dir, f"face_{timestamp}.jpg")
            cv2.imwrite(face_path, face_image)
            print(f"Novo rosto salvo: {face_path}")
            known_face_encodings.append(encoding)
            return len(known_face_encodings) - 1
        else:
            print("Rosto já detectado anteriormente.")
            return known_index
    return None

# -------------------------------
# Função de Detecção Integrada
# -------------------------------
def detect_objects(video_source, update_frame_callback, alert_callback, mode="live"):
    """
    Realiza a detecção de objetos e faces a partir do vídeo.

    Parâmetros:
      video_source: índice da câmera (0) ou caminho para arquivo de vídeo.
      update_frame_callback: função para atualizar o frame na interface.
      alert_callback: função para adicionar mensagens de alerta na interface.
      mode: "live" para monitoramento em tempo real ou "recorded" para análise de vídeo gravado.
    """
    global running, cap
    running = True
    model = YOLO('runs/detect/train/weights/best.pt')
    cap = cv2.VideoCapture(video_source)
    
    # Lista para acumular alertas (somente para modo "recorded")
    recorded_alerts = []
    
    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        dangerous_object_detected = False

        # Detecção de objetos com YOLO
        results = model(frame)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].numpy())
                confidence = box.conf[0]
                cls = box.cls[0]
                if confidence > 0.6:
                    label = f"{model.names[int(cls)]} {confidence:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    if model.names[int(cls)] in ['pistol', 'knife']:
                        dangerous_object_detected = True

        # Detecção de faces
        faces = face_recognition.face_locations(frame)
        for face_location in faces:
            face_encodings = face_recognition.face_encodings(frame, known_face_locations=[face_location])
            if face_encodings:
                encoding = face_encodings[0]
                index = get_known_face_index(encoding)
                # Modo "live": utiliza o envio imediato de alerta (com controle de 30 min)
                if mode == "live":
                    if index is None:
                        index = save_face(frame, face_location)
                        if index is None:
                            continue
                        if dangerous_object_detected:
                            alert_message = "⚠️ Alerta! Nova pessoa identificada com arma!"
                        else:
                            alert_message = "Nova pessoa identificada"
                    else:
                        if dangerous_object_detected:
                            alert_message = "🚨 Alerta Máximo! Pessoa já detectada anteriormente com arma. Todos aos seus postos"
                        else:
                            alert_message = "⚠️ Atençao! Pessoa já detectada anteriormente com arma. Fique atento!"
                    # Envia alerta somente se 30 minutos se passaram desde o último alerta para esse rosto
                    last_alert_time = face_last_alert.get(index)
                    if last_alert_time is None or (datetime.now() - last_alert_time) >= timedelta(minutes=30):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_path = os.path.join(captured_images_dir, f"alert_{timestamp}.jpg")
                        cv2.imwrite(image_path, frame)
                        threading.Thread(target=send_email, args=(image_path, alert_message)).start()
                        face_last_alert[index] = datetime.now()
                        alert_callback(alert_message)
                # Modo "recorded": agrupa os alertas e envia um único e-mail ao final
                elif mode == "recorded":
                    if index is None and dangerous_object_detected:
                        index = save_face(frame, face_location)
                        if index is None:
                            continue
                        alert_message = "Alerta! Nova pessoa identificada com arma!"
                        if alert_message not in recorded_alerts:
                            recorded_alerts.append(alert_message)
                        alert_callback(alert_message)
        # Atualiza o frame na interface (converte de BGR para RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        update_frame_callback(rgb_frame)
        cv2.waitKey(1)
    
    # Ao finalizar a análise do vídeo gravado, se houver alertas acumulados, envia um único e-mail com todas as detecções
    if mode == "recorded" and recorded_alerts:
        aggregated_message = "Alerta(s) de Vídeo Gravado:\n" + "\n".join(recorded_alerts)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(captured_images_dir, f"recorded_alert_{timestamp}.jpg")
        cv2.imwrite(image_path, frame)  # Utiliza o último frame capturado
        send_email(image_path, aggregated_message)
    stop_detection()

def stop_detection():
    """Interrompe a detecção e libera os recursos."""
    global cap, running
    running = False
    if cap:
        cap.release()
        cap = None
    cv2.destroyAllWindows()

# -------------------------------
# Interface Gráfica com Tkinter
# -------------------------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("VisionGuard - Monitoramento")
        self.root.configure(bg="#f0f0f0")
        
        # Área de exibição do vídeo
        self.video_label = tk.Label(root, bg="black")
        self.video_label.pack(padx=10, pady=10)
        
        # Painel de controles
        control_frame = tk.Frame(root, bg="#f0f0f0")
        control_frame.pack(pady=10)
        self.start_cam_btn = tk.Button(control_frame, text="Iniciar Câmera", command=self.start_camera, width=20, bg="#4CAF50", fg="white")
        self.start_cam_btn.grid(row=0, column=0, padx=5)
        self.open_video_btn = tk.Button(control_frame, text="Abrir Vídeo Gravado", command=self.open_video, width=20, bg="#2196F3", fg="white")
        self.open_video_btn.grid(row=0, column=1, padx=5)
        self.stop_btn = tk.Button(control_frame, text="Parar Monitoramento", command=self.stop_monitoring, width=20, bg="#f44336", fg="white")
        self.stop_btn.grid(row=0, column=2, padx=5)
        
        # Log de alertas
        self.alert_log = tk.Text(root, height=10, width=70, bg="white", fg="black")
        self.alert_log.pack(padx=10, pady=10)
        self.alert_log.insert(tk.END, "Log de alertas:\n")
        self.alert_log.config(state=tk.DISABLED)
        
        self.video_source = None
        self.detection_thread = None
        self.frame_image = None

    def start_camera(self):
        self.video_source = 0
        self.start_detection(mode="live")

    def open_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi")])
        if file_path:
            self.video_source = file_path
            self.start_detection(mode="recorded")

    def start_detection(self, mode="live"):
        if self.detection_thread is None or not self.detection_thread.is_alive():
            self.detection_thread = threading.Thread(
                target=detect_objects,
                args=(self.video_source, self.update_frame, self.add_alert, mode),
                daemon=True
            )
            self.detection_thread.start()

    def stop_monitoring(self):
        stop_detection()

    def update_frame(self, frame):
        """Atualiza o widget de vídeo com o frame recebido."""
        image = Image.fromarray(frame)
        self.frame_image = ImageTk.PhotoImage(image=image)
        self.video_label.config(image=self.frame_image)

    def add_alert(self, message):
        """Adiciona uma mensagem de alerta no log da interface."""
        def _update():
            self.alert_log.config(state=tk.NORMAL)
            current_time = datetime.now().strftime("%H:%M:%S")
            self.alert_log.insert(tk.END, f"{current_time} - {message}\n")
            self.alert_log.see(tk.END)
            self.alert_log.config(state=tk.DISABLED)
        self.root.after(0, _update)

# -------------------------------
# Execução Principal
# -------------------------------
if __name__ == "__main__":
    load_known_faces()  # Carrega os rostos já salvos para o cache
    root = tk.Tk()
    app = App(root)
    root.mainloop()
