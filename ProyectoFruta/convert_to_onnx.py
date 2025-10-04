import torch
import torch.nn as nn
from torchvision import models
import argparse
import os
from tqdm import tqdm

# =====================
# ARGUMENTOS
# =====================
parser = argparse.ArgumentParser(description="Convertir modelo entrenado a ONNX")
parser.add_argument("--model", type=str, default="resnet18",
                    choices=["resnet18", "mobilenetv2", "efficientnet_b0"],
                    help="Modelo base usado en el entrenamiento")
parser.add_argument("--dataset", type=str, default="dataset/train",
                    help="Ruta al dataset para detectar clases automáticamente")
parser.add_argument("--weights", type=str, default="best_model.pth",
                    help="Archivo .pth con los pesos entrenados")
parser.add_argument("--output", type=str, default="modelo_manzana.onnx",
                    help="Nombre del archivo de salida ONNX")
args = parser.parse_args()

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =====================
# DETECTAR CLASES
# =====================
num_classes = len(os.listdir(args.dataset))
class_names = os.listdir(args.dataset)
print(f"\n📂 Se detectaron {num_classes} clases: {class_names}")

# =====================
# CREAR MODELO
# =====================
if args.model == "resnet18":
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
elif args.model == "mobilenetv2":
    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
elif args.model == "efficientnet_b0":
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)

# Cargar pesos
model.load_state_dict(torch.load(args.weights, map_location=DEVICE))
model = model.to(DEVICE)
model.eval()

# =====================
# INFO DEL MODELO
# =====================
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"\n🧠 Modelo: {args.model}")
print(f"🔢 Parámetros totales: {total_params:,}")
print(f"⚙️ Parámetros entrenables: {trainable_params:,}")
print(f"🎯 Número de clases: {num_classes}")

# =====================
# EXPORTAR A ONNX
# =====================
print("\n🚀 Exportando a ONNX...")
dummy_input = torch.randn(1, 3, 224, 224).to(DEVICE)

for _ in tqdm(range(100), desc="Progreso exportación", ncols=100):
    pass  # Solo para animación

torch.onnx.export(
    model,
    dummy_input,
    args.output,
    export_params=True,
    opset_version=11,
    do_constant_folding=True,
    input_names=["input"],
    output_names=["output"]
)

print(f"✅ Modelo exportado correctamente a {args.output}")

# =====================
# VERIFICACIÓN ONNX
# =====================
try:
    import onnx
    import onnxruntime as ort

    print("\n🔍 Verificando integridad del modelo ONNX...")

    # Validación ONNX
    onnx_model = onnx.load(args.output)
    onnx.checker.check_model(onnx_model)
    print("✅ Validación ONNX: OK")

    # Probar inferencia rápida
    ort_session = ort.InferenceSession(args.output)
    test_input = dummy_input.cpu().numpy()
    outputs = ort_session.run(None, {"input": test_input})
    print(f"⚡ Inference de prueba OK. Salida shape: {outputs[0].shape}")

except ImportError:
    print("⚠️ onnxruntime no está instalado. Ejecuta: pip install onnx onnxruntime")

print("\n🎉 Conversión finalizada con éxito")
