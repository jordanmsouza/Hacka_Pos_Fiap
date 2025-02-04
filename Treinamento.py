from ultralytics import YOLO


# Function to train YOLOv8 model
def train_model():
    model = YOLO('yolov8n.pt')  # Load YOLOv8 pre-trained model
    model.train(data='C:/Users/Public/Documents/Dataset/dataset.yaml', epochs=50, imgsz=640)  # Specify dataset and parameters
    model.export(format='onnx')  # Export model for deployment

# Main Script
if __name__ == "__main__":
    train_model()  # Train model
