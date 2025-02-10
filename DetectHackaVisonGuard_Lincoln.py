DetectHackaVisonGuard-1.py
import os
import re
import cv2
import threading
import smtplib
import mimetypes
import face_recognition
from datetime import datetime, timedelta
from ultralytics import YOLO
from email.message import EmailMessage
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import numpy as np

# -------------------------------
# Configuração do e-mail
# -------------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "securytevisionguard@gmail.com"  # Substitua pelo seu e-mail
EMAIL_PASSWORD = "qihv lyhu ajng gncr"           # Substitua pela senha de aplicativo do Gmail
EMAIL_RECEIVER = "lincoln.soa@gmail.com"

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

# Cache para armazenar os encodings dos rostos já salvos
known_face_encodings = []
# Dicionário que mapeia o índice do rosto para o último horário em que o alerta foi enviado (modo live)
face_last_alert = {}
# Dicionário para armazenar o timestamp (extraído do nome da imagem) da primeira detecção com arma para cada rosto
# Formato: "YYYY-MM-DD HH:MM:SS"
face_detection_time = {}
# Dicionário para contar quantos frames consecutivos um rosto foi detectado sem arma
face_no_weapon_counter = {}
# Conjunto para registrar quais alertas únicos já foram exibidos na interface
unique_gui_alerts = set()

# -------------------------------
# Funções Auxiliares
# -------------------------------
def load_known_faces():
    """
    Carrega os rostos já salvos no cache a partir da pasta detected_faces
    e extrai o timestamp dos nomes dos arquivos para preencher o dicionário face_detection_time.
    """
    global known_face_encodings, face_detection_time
    files = sorted(os.listdir(detected_faces_dir))
    for file in files:
        if file.startswith("face_") and file.endswith(".jpg"):
            image_path = os.path.join(detected_faces_dir, file)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                index = len(known_face_encodings)
                known_face_encodings.append(encodings[0])
                # Extrai o timestamp do nome do arquivo (formato: face_YYYYMMDD_HHMMSS.jpg)
                match = re.search(r'face_(\d{8}_\d{6})\.jpg', file)
                if match:
                    filename_timestamp = match.group(1)
                    dt = datetime.strptime(filename_timestamp, "%Y%m%d_%H%M%S")
                    formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                    face_detection_time[index] = formatted_timestamp
    # print(f"{len(known_face_encodings)} rostos conhecidos carregados.")

def send_email(image_path, alert_message):
    msg = EmailMessage()
    msg["Subject"] = "🚨 Alerta de Detecção! 🚨"  # Assunto fixo para todos os e-mails
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    msg.set_content(f"Alerta Geral!\n\n{alert_message}")

    
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

def send_email_multiple(image_paths, alert_message):
    msg = EmailMessage()
    msg["Subject"] = "🚨 Alerta de Detecção! 🚨"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    msg.set_content(f"Alerta Geral!\n\n{alert_message}")

    for image_path in image_paths:
        ctype, encoding = mimetypes.guess_type(image_path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(image_path, "rb") as img:
            msg.add_attachment(img.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(image_path))
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
    Salva a face detectada na pasta detected_faces, caso seja nova, e atualiza o cache.
    O nome do arquivo inclui o timestamp (gerado apenas na primeira detecção).
    Retorna o índice do rosto no cache.
    """
    face_encodings = face_recognition.face_encodings(frame, known_face_locations=[face_location])
    if face_encodings:
        encoding = face_encodings[0]
        known_index = get_known_face_index(encoding)
        if known_index is None:
            top, right, bottom, left = face_location
            face_image = frame[top:bottom, left:right]
            # Gera o timestamp para o nome do arquivo (único para a primeira detecção)
            filename_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            face_path = os.path.join(detected_faces_dir, f"face_{filename_timestamp}.jpg")
            cv2.imwrite(face_path, face_image)
            print(f"Novo rosto salvo: {face_path}")
            new_index = len(known_face_encodings)
            known_face_encodings.append(encoding)
            dt = datetime.strptime(filename_timestamp, "%Y%m%d_%H%M%S")
            formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            face_detection_time[new_index] = formatted_timestamp
            return new_index
        else:
            print("Rosto já detectado anteriormente.")
            return known_index
    return None

# -------------------------------
# Função de Detecção Integrada
# -------------------------------
def detect_objects(video_source, update_frame_callback, alert_callback, mode="live"):
    global running, cap, unique_gui_alerts, face_no_weapon_counter
    running = True
    model = YOLO('runs/detect/train/weights/best.pt')
    cap = cv2.VideoCapture(video_source)
    
    temporal_detection_history = []
    # Para modo recorded: lista para armazenar os caminhos dos frames com arma detectada
    captured_frames = []
    
    NO_WEAPON_THRESHOLD = 3
    
    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Correção de Iluminação e Redução de Ruídos
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        lab = cv2.merge((cl, a, b))
        frame_corrected = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        frame_processed = cv2.fastNlMeansDenoisingColored(frame_corrected, None, 10, 10, 7, 21)

        dangerous_object_detected = False
        label = None

        # Detecção de objetos com YOLO
        results = model(frame_processed)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].numpy())
                confidence = box.conf[0]
                cls = box.cls[0]
                if confidence > 0.6:
                    label = f"{model.names[int(cls)]} {confidence:.2f}"
                    cv2.rectangle(frame_processed, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame_processed, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    # Verifica se o objeto detectado é uma arma (pode incluir outras classes, se necessário)
                    if model.names[int(cls)] in ['pistol', 'knife']:
                        dangerous_object_detected = True
                        # Atualiza o log na interface (como no modo live)
                        alert_callback(f"Objeto perigoso detectado: {label}")

        temporal_detection_history.append(1 if dangerous_object_detected else 0)
        if len(temporal_detection_history) > 5:
            temporal_detection_history.pop(0)
        confirmed_dangerous = True if sum(temporal_detection_history) >= 2 else False

        # Detecção de faces (mantém a lógica para atualização dos logs na interface)
        faces = face_recognition.face_locations(frame_processed)
        for face_location in faces:
            face_encodings = face_recognition.face_encodings(frame_processed, known_face_locations=[face_location])
            if face_encodings:
                encoding = face_encodings[0]
                index = get_known_face_index(encoding)
                if mode == "live":
                    # Lógica do modo live (permanece inalterada)
                    if index is None:
                        if confirmed_dangerous:
                            index = save_face(frame_processed, face_location)
                            if index is None:
                                continue
                            alert_message = "Suspeito armado identificado! \nDirijam-se imediatamente ao local!"
                        else:
                            continue
                    else:
                        if confirmed_dangerous:
                            face_no_weapon_counter[index] = 0
                            if index not in face_detection_time:
                                continue
                            first_detection_time = face_detection_time[index]
                            alert_message = (f"Suspeito, previamente detectado portando arma em "
                                             f"{first_detection_time}, foi avistado novamente em nossas instalações. \n\nPermançam em seus postos e tomem cuidado. \n\nSuspeito está armado!")
                        else:
                            current_count = face_no_weapon_counter.get(index, 0) + 1
                            face_no_weapon_counter[index] = current_count
                            if current_count >= NO_WEAPON_THRESHOLD:
                                if index not in face_detection_time:
                                    continue
                                first_detection_time = face_detection_time[index]
                                alert_message = (f"Suspeito, previamente detectado portando arma em "
                                                 f"{first_detection_time}, foi visto novamente em nossas instalações. \n\nEmbora não tenha sido detectada a presença de armas no momento, o suspeito pode ser perigoso. \n\nTenham cuidado!")
                                face_no_weapon_counter[index] = 0
                            else:
                                continue

                    last_alert_time = face_last_alert.get(index)
                    if last_alert_time is None or (datetime.now() - last_alert_time) >= timedelta(minutes=30):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_path = os.path.join(captured_images_dir, f"alert_{timestamp}.jpg")
                        cv2.imwrite(image_path, frame_processed)
                        threading.Thread(target=send_email, args=(image_path, alert_message)).start()
                        face_last_alert[index] = datetime.now()
                        if alert_message not in unique_gui_alerts:
                            alert_callback(alert_message)
                            unique_gui_alerts.add(alert_message)
                elif mode == "recorded":
                    # No modo recorded, a lógica de faces permanece apenas para atualizar os logs na interface
                    if confirmed_dangerous:
                        # Atualiza o log com a detecção, semelhante ao live
                        alert_callback(f"Objeto perigoso detectado: {label}")
                        # Caso o alerta padrão ainda não tenha sido exibido na interface, exibe-o
                        standard_alert = "⚠️ Alerta! Suspeito identificado com arma!"
                        if standard_alert not in unique_gui_alerts:
                            alert_callback(standard_alert)
                            unique_gui_alerts.add(standard_alert)

        # **Lógica para salvar o frame quando uma arma for detectada (para modo recorded)**
        if mode == "recorded" and confirmed_dangerous:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(captured_images_dir, f"alert_{timestamp}.jpg")
            cv2.imwrite(image_path, frame_processed)
            # Adiciona o caminho do frame à lista se ainda não estiver presente
            if image_path not in captured_frames:
                captured_frames.append(image_path)

        # Atualiza o frame na interface
        rgb_frame = cv2.cvtColor(frame_processed, cv2.COLOR_BGR2RGB)
        update_frame_callback(rgb_frame)
        cv2.waitKey(1)
    
    # Ao final do vídeo (modo recorded), se houver frames com detecções, envia um e-mail agrupado
    if mode == "recorded" and captured_frames:
        aggregated_message = "Alerta(s) de Vídeo Gravado:\nForam detectadas as seguintes ocorrências de armas perigosas."
        send_email_multiple(captured_frames, aggregated_message)
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
# Interface Gráfica com Tkinter - Versão Aprimorada
# -------------------------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("VisionGuard - Monitoramento")
        self.root.configure(bg="#f0f0f0")
        self.root.geometry("900x600")
        self.root.minsize(600, 400)
        
        # Configura o estilo com ttk
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        
        # Configuração da grid para responsividade
        self.root.columnconfigure(0, weight=1)
        for i in range(4):
            self.root.rowconfigure(i, weight=1)
        
        # Cabeçalho com título
        header = ttk.Label(root, text="VisionGuard - Monitoramento", font=("Helvetica", 20, "bold"), background="#f0f0f0")
        header.grid(row=0, column=0, pady=(10,5), sticky="ew")
        
        # Frame principal para o conteúdo (vídeo)
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        
        # Área de exibição do vídeo
        self.video_label = ttk.Label(self.main_frame, background="black")
        self.video_label.grid(row=0, column=0, sticky="nsew")
        
        # Painel de controle inferior com botões
        control_frame = ttk.Frame(root, padding=10)
        control_frame.grid(row=2, column=0, pady=5, sticky="ew")
        control_frame.columnconfigure((0,1,2,3), weight=1)
        
        self.start_cam_btn = ttk.Button(control_frame, text="Iniciar Câmera", command=self.start_camera)
        self.start_cam_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.open_video_btn = ttk.Button(control_frame, text="Abrir Vídeo Gravado", command=self.open_video)
        self.open_video_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.stop_btn = ttk.Button(control_frame, text="Parar Monitoramento", command=self.stop_monitoring)
        self.stop_btn.grid(row=0, column=2, padx=5, sticky="ew")
        
        self.exit_btn = ttk.Button(control_frame, text="Sair", command=self.exit_application)
        self.exit_btn.grid(row=0, column=3, padx=5, sticky="ew")
        
        # Log de alertas com rolagem
        log_frame = ttk.Frame(root, padding=(10,0,10,10))
        log_frame.grid(row=3, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.alert_log = tk.Text(log_frame, height=8, wrap="word", background="white", foreground="black")
        self.alert_log.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.alert_log.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.alert_log['yscrollcommand'] = scrollbar.set
        self.alert_log.insert(tk.END, "Log de alertas:\n")
        self.alert_log.config(state=tk.DISABLED)
        
        # Variáveis de controle
        self.video_source = None
        self.detection_thread = None
        self.frame_image = None

        # Permite que o fechamento da janela seja tratado pelo método exit_application
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)

    def start_camera(self):
        self.video_source = 0
        self.start_detection(mode="live")

    def open_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi")])
        if file_path:
            self.video_source = file_path
            self.start_detection(mode="recorded")

    def start_detection(self, mode="live"):
        global unique_gui_alerts
        unique_gui_alerts.clear()
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
        """Atualiza o widget de vídeo com o frame recebido, redimensionando a imagem conforme o tamanho do widget."""
        # Obtém as dimensões atuais do widget de vídeo
        label_width = self.video_label.winfo_width()
        label_height = self.video_label.winfo_height()
        image = Image.fromarray(frame)
        if label_width > 0 and label_height > 0:
            image = image.resize((label_width, label_height), Image.Resampling.LANCZOS)
        self.frame_image = ImageTk.PhotoImage(image=image)
        self.video_label.config(image=self.frame_image)
        self.video_label.image = self.frame_image  # previne coleta de lixo

    def add_alert(self, message):
        """Adiciona uma mensagem de alerta no log da interface."""
        def _update():
            self.alert_log.config(state=tk.NORMAL)
            current_time = datetime.now().strftime("%H:%M:%S")
            self.alert_log.insert(tk.END, f"{current_time} - {message}\n")
            self.alert_log.see(tk.END)
            self.alert_log.config(state=tk.DISABLED)
        self.root.after(0, _update)
    
    def exit_application(self):
        """Encerra a aplicação, liberando os recursos."""
        stop_detection()
        self.root.destroy()

# -------------------------------
# Execução Principal
# -------------------------------
if __name__ == "__main__":
    load_known_faces()  # Carrega os rostos já salvos para o cache e extrai seus timestamps
    root = tk.Tk()
    app = App(root)
    root.mainloop()
