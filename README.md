# VisionGuard - Detecção de Objetos Perigosos

## Descrição

VisionGuard é um sistema de visão computacional baseado em YOLO que detecta objetos perigosos, como facas e pistolas, em tempo real. Quando um objeto suspeito é identificado, o sistema captura uma imagem e envia uma notificação por e-mail usando a API do SendGrid.

## Funcionalidades

- Detecção de objetos cortantes e armas em tempo real
- Suporte a câmera ao vivo e vídeos pré-gravados
- Envio automático de alertas por e-mail com imagem anexada
- Interface gráfica para facilitar o uso

## Tecnologias Utilizadas

- **Python**
- **OpenCV**
- **YOLO** (You Only Look Once)
- **SMTP (Gmail)**: Protocolo para envio de e-mails.
- **Tkinter** (interface gráfica)

## Requisitos

Antes de executar o projeto, certifique-se de ter instalado os seguintes pacotes:

```bash
pip install opencv-python sendgrid ultralytics tkinter
```

## Como Usar

### Modo Câmera

1. Execute o script principal:
   ```bash
   python visionguard.py
   ```
2. Clique no botão "Câmera" para iniciar a detecção ao vivo.
3. Pressione `q` ou `Esc` para encerrar.

### Modo Vídeo

1. Execute o script e clique no botão "Vídeo".
2. Selecione um arquivo de vídeo (`.mp4`, `.avi` etc.).
3. Aguarde a análise e o envio de alertas, se necessário.

## Estrutura do Código

- `detect_objects(video_source)`: Realiza a detecção de objetos em tempo real.
- `send_email(image_path)`: Envia um e-mail com a imagem capturada pelo SendGrid.
- `stop_detection()`: Encerra a captura de vídeo corretamente.
- `App`: Interface gráfica com botões para iniciar/parar a detecção.

## Acesso ao Dataset

O dataset utilizado para treinamento do modelo pode ser acessado no Google Drive através do seguinte link:
[Dataset VisionGuard](https://drive.google.com/drive/folders/13qi71kzV0WxuKdReM01d0W-EU7aWyEg6?usp=sharing)

## Contribuição

Sinta-se à vontade para sugerir melhorias ou relatar problemas através de **Issues** ou **Pull Requests**.

## Licença

Este projeto está licenciado sob a **MIT License**

