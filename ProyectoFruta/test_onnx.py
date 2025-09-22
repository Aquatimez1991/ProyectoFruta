import onnxruntime as ort
from PIL import Image
import torchvision.transforms as transforms

# Clases (asegúrate de que coincidan con las de tu dataset)
class_names = ["buena", "mala"]

# Cargar modelo ONNX
session = ort.InferenceSession("modelo_manzana.onnx")

# Preprocesamiento de la imagen (igual que en train/val)
transform = transforms.Compose([
    transforms.Resize((224, 224)),  # 👈 ahora a 224x224
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])  # 👈 RGB, no 1 solo canal
])


def predict(image_path):
    image = Image.open(image_path).convert("RGB")
    img_tensor = transform(image).unsqueeze(0).numpy()

    inputs = {session.get_inputs()[0].name: img_tensor}
    outputs = session.run(None, inputs)
    pred = outputs[0]
    pred_class = pred.argmax(axis=1)[0]
    return class_names[pred_class]

# Ejemplo de prueba
if __name__ == "__main__":
    print("Predicción:", predict("ejemplo.jpg"))  # coloca aquí tu imagen de prueba
