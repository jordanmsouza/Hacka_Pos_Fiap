
# **VisionGuard - Sistema de Monitoramento Inteligente**

## **Descrição Geral**
O **VisionGuard** é um sistema de monitoramento baseado em visão computacional, projetado para identificar rostos, detectar objetos perigosos (como armas e facas) e enviar alertas em tempo real via e-mail. Utilizando modelos de detecção YOLO para objetos e a biblioteca `face_recognition` para reconhecimento facial, o sistema visa garantir segurança de maneira proativa e automatizada.

Além disso, o sistema oferece uma interface gráfica (GUI) desenvolvida em `Tkinter`, facilitando o uso tanto para monitoramento em tempo real quanto para análise de vídeos gravados.

---

## **Principais Funcionalidades**
- **Detecção de Objetos Perigosos:** Utiliza o modelo YOLO para identificar objetos como facas e armas de fogo em vídeo.
- **Reconhecimento Facial:** Detecta e armazena rostos desconhecidos, atualizando um cache para evitar alertas duplicados em um intervalo menor que 30 minutos.
- **Envio de Alertas por E-mail:** Envia automaticamente imagens das detecções críticas com mensagens personalizadas de alerta.
- **Modo de Operação Duplo:**
  - **Monitoramento ao vivo:** Processa imagens de uma câmera ao vivo e envia alertas em tempo real.
  - **Análise de vídeos gravados:** Gera um resumo de todas as detecções em um único e-mail ao final do vídeo.
- **Interface Gráfica Simples e Intuitiva:** Permite iniciar/parar o monitoramento e visualizar logs de alertas em tempo real.

---

## **Estrutura do Código**
1. **Configuração de E-mail:**  
   Configura o envio de e-mails para notificações, utilizando o servidor SMTP do Gmail.

2. **Carregamento de Dados:**  
   - Carrega rostos previamente salvos para evitar alertas duplicados.
   - Cria pastas para armazenar as faces detectadas e capturas de imagens.

3. **Detecção e Reconhecimento:**  
   - A função `detect_objects` realiza a detecção de objetos e rostos.
   - Em caso de detecção de um objeto perigoso, o sistema salva a imagem e envia um e-mail de alerta.

4. **Interface Gráfica (GUI):**  
   Desenvolvida com `Tkinter`, oferece controles para iniciar a câmera, carregar vídeos gravados e exibir logs de alertas.

5. **Execução Principal:**  
   O programa inicia carregando rostos conhecidos e, em seguida, exibe a interface gráfica para interação do usuário.

---

## **Bibliotecas Utilizadas**
- **`os` e `threading`**: Gerenciamento de arquivos e controle de threads.
- **`cv2` (OpenCV)**: Manipulação e captura de vídeo.
- **`face_recognition`**: Reconhecimento facial.
- **`ultralytics`**: Detecção de objetos com YOLO.
- **`smtplib` e `email`**: Envio de e-mails com anexos.
- **`tkinter` e `PIL` (Pillow)**: Criação da interface gráfica e exibição de vídeo.
- **`numpy`**: Manipulação de arrays de imagens.

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

## Requisitos

Antes de executar o projeto, certifique-se de ter instalado os seguintes pacotes:

```bash```
pip install opencv-python ultralytics tkinter Pillow face_recognition

---

## **Como Utilizar**
1. Execute o código em Python (`python DetectHackaVisonGuard_Lincoln.py`).
2. Utilize a interface para:
   - Iniciar a câmera ao vivo para monitoramento em tempo real.
   - Abrir um vídeo gravado para análise posterior.
   - Visualizar o log de alertas diretamente na interface.

3. O sistema enviará um e-mail com a imagem capturada sempre que detectar uma situação crítica.

---

## **Observações**
- O modelo YOLO utilizado está localizado no caminho `runs/detect/train/weights/best.pt`. Certifique-se de que ele está disponível para uso.
- O tempo mínimo entre alertas para o mesmo rosto é de **30 minutos**, para evitar múltiplas notificações em curto intervalo.

---

## Acesso ao Dataset

O dataset utilizado para treinamento do modelo pode ser acessado no Google Drive através do seguinte link:
[Dataset VisionGuard](https://drive.google.com/drive/folders/13qi71kzV0WxuKdReM01d0W-EU7aWyEg6?usp=sharing)

---

## Contribuição

Sinta-se à vontade para sugerir melhorias ou relatar problemas através de **Issues** ou **Pull Requests**.

---

## Licença

Este projeto está licenciado sob o **Apache 2.0 License**
