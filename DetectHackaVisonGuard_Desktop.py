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

# Configuração do e-mail
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "securytevisionguard@gmail.com"  
EMAIL_PASSWORD = "qihv lyhu ajng gncr"  
EMAIL_RECEIVER = "jordanmam29@gmail.com" 

# Variáveis globais para controle
running = False
paused = False
cap = None  
alert_sent = False  # para alerta imediato no modo câmera

# Lock para sincronização de escrita de imagens
lock = threading.Lock()

# Função para enviar e-mail (modo câmera)
def send_email(image_path):
    msg = EmailMessage()
    msg["Subject"] = "⚠️ Alerta de Objeto Perigoso Detectado!"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content("Um objeto perigoso foi detectado pela câmera. A imagem está anexada.")

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

# Função para enviar e-mail com alertas de vídeo (anexando todas as imagens)
def send_email_video_alert(detections, image_paths):
    msg = EmailMessage()
    msg["Subject"] = "⚠️ Alerta de Vídeo: Objetos Perigosos Detectados"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    conteudo = "Os objetos abaixo foram detectados no vídeo:\n" + ", ".join(detections)
    msg.set_content(conteudo)
    
    for image_path in image_paths:
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
        print("E-mail de análise de vídeo enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail de análise de vídeo: {e}")

# Função de detecção – usada tanto para câmera quanto para vídeo
def detect_objects(video_source=0):
    global running, paused, cap, alert_sent
    running = True  
    model = YOLO('runs/detect/train/weights/best.pt')  
    cap = cv2.VideoCapture(video_source)
    if cap is None or not cap.isOpened():
        print("Erro: Não foi possível abrir a fonte de vídeo ou câmera.")
        running = False
        return

    captured_images_dir = "captured_images"
    os.makedirs(captured_images_dir, exist_ok=True)
    
    # Define se a fonte é vídeo (arquivo) ou câmera (índice numérico)
    is_video = isinstance(video_source, str)
    # Para vídeos: manter contagem de frames consecutivos e armazenar imagens de alerta
    consecutive_counts = {}  # chave: label -> contagem de frames consecutivos
    valid_detections = set()   # objetos com >= 3 frames consecutivos
    alert_images = []          # lista com os caminhos das imagens salvas
    
    last_frame = None  # armazenará o último frame lido

    while cap.isOpened():
        if not running:
            break

        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            last_frame = frame.copy()
            
            # Processa a detecção somente se não estiver pausado
            results = model(frame)
            unique_labels = set() if is_video else None

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].numpy()
                    confidence = box.conf[0]
                    cls = box.cls[0]
                    if confidence > 0.6:
                        label_text = f"{model.names[int(cls)]} {confidence:.2f}"
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                        cv2.putText(frame, label_text, (int(x1), int(y1) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        objeto_atual = model.names[int(cls)]
                        # Filtra para os objetos de interesse
                        if objeto_atual in ['knife', 'pistol']:
                            if is_video:
                                unique_labels.add(objeto_atual)
                            else:
                                if not alert_sent:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    image_path = os.path.join(captured_images_dir, f"suspect_{timestamp}.jpg")
                                    with lock:
                                        cv2.imwrite(image_path, frame)
                                        print(f"Imagem salva: {image_path}")
                                        threading.Thread(target=send_email, args=(image_path,)).start()
                                        alert_sent = True

            if is_video:
                # Atualiza as contagens para os objetos detectados
                for label in list(consecutive_counts.keys()):
                    if label in unique_labels:
                        consecutive_counts[label] += 1
                    else:
                        consecutive_counts[label] = 0
                for label in unique_labels:
                    if label not in consecutive_counts:
                        consecutive_counts[label] = 1
                # Se algum objeto atingir exatamente 3 frames consecutivos, salva o frame atual (uma vez por frame)
                frame_alert_saved = False
                for label in unique_labels:
                    if consecutive_counts[label] == 3:
                        valid_detections.add(label)
                        if not frame_alert_saved:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            image_path = os.path.join(captured_images_dir, f"video_alert_{label}_{timestamp}.jpg")
                            cv2.imwrite(image_path, frame)
                            alert_images.append(image_path)
                            frame_alert_saved = True
                            print(f"Imagem de alerta salva: {image_path}")
                print(f"Frame: {datetime.now().strftime('%H:%M:%S')}, unique_labels: {unique_labels}")
                #print(f"Contagens atuais: {consecutive_counts}")
                #print(f"Detecções válidas até agora: {valid_detections}")
        else:
            # Se estiver pausado, não atualiza o frame: usa o último frame lido (se houver) e insere o texto "Paused"
            if last_frame is not None:
                frame = last_frame.copy()
                cv2.putText(frame, "Paused", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 2)
            else:
                # Se ainda não há frame, espera um pouco
                cv2.waitKey(100)
                continue

        cv2.imshow('Detection', frame)
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q') or key == 27:
            running = False
            break

        # Verifica se a janela foi fechada pelo usuário
        if cv2.getWindowProperty('Detection', cv2.WND_PROP_VISIBLE) < 1:
            print("Janela 'Detection' fechada pelo usuário.")
            running = False
            break

    # No modo vídeo, se houver detecções, envia o e-mail com todas as imagens coletadas
    if is_video and valid_detections and alert_images:
        send_email_video_alert(valid_detections, alert_images)
    else:
        if is_video:
            print("Nenhuma detecção válida para enviar e-mail.")

    stop_detection()

# Função para liberar recursos e fechar janelas
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
        self.root.geometry("400x300")

        self.label = tk.Label(root, text="Selecione a fonte de vídeo:", font=("Arial", 14))
        self.label.pack(pady=10)

        self.camera_button = tk.Button(root, text="Iniciar câmera", command=self.start_camera, width=20)
        self.camera_button.pack(pady=5)

        self.video_button = tk.Button(root, text="Selecionar vídeo", command=self.open_video, width=20)
        self.video_button.pack(pady=5)

        # Botões para pausar e retomar a captura/detecção
        self.pause_button = tk.Button(root, text="Pausar detecção", command=self.pause_monitoring, width=20)
        self.pause_button.pack(pady=5)
        self.start_button = tk.Button(root, text="Iniciar detecção", command=self.resume_monitoring, width=20)
        self.start_button.pack(pady=5)

        self.quit_button = tk.Button(root, text="Fechar aplicação", command=self.quit_app, width=20)
        self.quit_button.pack(pady=5)

        self.thread = None  

    def start_camera(self):
        global running, alert_sent, paused
        if not running:
            alert_sent = False  # Reinicia alerta para câmera
            paused = False
            self.thread = threading.Thread(target=detect_objects, args=(0,), daemon=True)
            self.thread.start()

    def open_video(self):
        global running, paused
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi")])
        if file_path and not running:
            paused = False
            self.thread = threading.Thread(target=detect_objects, args=(file_path,), daemon=True)
            self.thread.start()

    def pause_monitoring(self):
        global paused
        paused = True
        print("Monitoramento pausado.")

    def resume_monitoring(self):
        global paused
        paused = False
        print("Monitoramento retomado.")

    def quit_app(self):
        stop_detection()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()
