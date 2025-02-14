
# **VisionGuard - Sistema de Monitoramento Inteligente**

## **Descrição Geral**
O **VisionGuard** é um sistema de monitoramento baseado em visão computacional, projetado para detectar objetos cortantes (como facas, tesouras e estiletes) e enviar alertas em tempo real via e-mail. Utilizando o modelo YOLO para a detecção, o sistema visa garantir segurança de maneira proativa e automatizada.

Além disso, o sistema oferece uma interface gráfica (GUI) desenvolvida em `Tkinter`, facilitando o uso tanto para monitoramento em tempo real quanto para análise de vídeos gravados.

---

## **Principais Funcionalidades**
- **Detecção de Objetos Cortantes:** Utiliza o modelo YOLO para identificar objetos como facas e armas de fogo em vídeo.
- **Envio de Alertas por E-mail:** Envia automaticamente imagens das detecções críticas com mensagens personalizadas de alerta.
- **Modo de Operação Duplo:**
  - **Monitoramento ao vivo:** Processa imagens de uma câmera ao vivo e envia alertas em tempo real.
  - **Análise de vídeos gravados:** Gera um resumo de todas as detecções em um único e-mail ao final do vídeo.
- **Interface Gráfica Simples e Intuitiva:** Permite iniciar/parar o monitoramento, pausar e retomar a detecção.

---

## **Estrutura do Código**
1. **Configuração de E-mail:**  
   Configura o envio de e-mails para notificações, utilizando o servidor SMTP do Gmail.

2. **Detecção de Objetos:**  
   - A função `detect_objects` realiza a detecção de objetos cortantes.
   - Em caso de detecção, o sistema salva a imagem e envia um e-mail de alerta.

3. **Interface Gráfica (GUI):**  
   Desenvolvida com `Tkinter`, oferece controles para iniciar a câmera, carregar vídeos gravados, pausar e retomar o monitoramento.

4. **Execução Principal:**  
   O programa inicia exibindo a interface gráfica para interação do usuário.

---

## **Bibliotecas Utilizadas**
- **`os` e `threading`**: Gerenciamento de arquivos e controle de threads.
- **`cv2` (OpenCV)**: Manipulação e captura de vídeo.
- **`ultralytics`**: Detecção de objetos com YOLO.
- **`smtplib` e `email`**: Envio de e-mails com anexos.
- **`tkinter`**: Criação da interface gráfica.
- **`mimetypes`**: Identificação do tipo de arquivo para anexos.
- **`datetime`**: Manipulação de datas e horários.

---

## **Configuração Inicial**
- Crie uma conta de e-mail para envio de notificações e habilite a senha de aplicativo no Gmail.
- Insira as credenciais do e-mail no código:
  ```python
  EMAIL_SENDER = "seu_email@gmail.com"
  EMAIL_PASSWORD = "sua_senha_de_aplicativo"
  EMAIL_RECEIVER = "email_do_destinatário"
  ```

---

## **Requisitos**

Antes de executar o projeto, certifique-se de ter instalado os seguintes pacotes:

```bash
pip install opencv-python ultralytics tkinter
```

---

## **Como Utilizar**
1. Execute o código em Python (`python DetectHackaVisonGuard_Desktop.py`).
2. Utilize a interface para:
   - Iniciar a câmera ao vivo para monitoramento em tempo real.
   - Abrir um vídeo gravado para análise posterior.
   - Pausar e retomar o monitoramento a qualquer momento.

3. O sistema enviará um e-mail com a imagem capturada sempre que detectar uma situação crítica.

---

## **Observações**
- O modelo YOLO utilizado está localizado no caminho `runs/detect/train/weights/best.pt`. Certifique-se de que ele está disponível para uso.
- As detecções válidas para envio de alerta incluem **facas** e **armas**.

---

## Acesso ao Dataset e ao video explicativo do projeto

O dataset utilizado para treinamento do modelo pode ser acessado no Google Drive através do seguinte link:
[Dataset VisionGuard](https://drive.google.com/drive/folders/13qi71kzV0WxuKdReM01d0W-EU7aWyEg6?usp=sharing).

Para acesso ao video explicativo desse projeto, acesse através do seguinte link:
[Video Explicativo Youtube](https://youtu.be/-ptQVMex2xI?si=19KDhoERRBA259it).

---

## Contribuição

Sinta-se à vontade para sugerir melhorias ou relatar problemas através de **Issues** ou **Pull Requests**.

---

## Licença

Este projeto está licenciado sob o **Apache 2.0 License**
