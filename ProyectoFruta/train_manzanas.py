import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from torch.cuda.amp import GradScaler, autocast
from tqdm import tqdm  # 🔹 Barra de progreso

# =====================
# CONFIGURACIÓN GENERAL
# =====================
DATA_DIR = "dataset"  # Ajusta si tu dataset está en otra carpeta
BATCH_SIZE = 32
NUM_EPOCHS = 20
LEARNING_RATE = 0.001

# Transformaciones
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

# Dataset
train_dataset = datasets.ImageFolder(DATA_DIR + "/train", transform=transform)
val_dataset = datasets.ImageFolder(DATA_DIR + "/val", transform=transform)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE,
                          shuffle=True, num_workers=0, pin_memory=True)  # 🔹 num_workers=0 en Windows
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE,
                        shuffle=False, num_workers=0, pin_memory=True)

# =====================
# SELECCIÓN DE MODELO
# =====================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🔹 Usando dispositivo: {device}")

# 🔹 Modelo recomendado (ResNet18)
model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
model.fc = nn.Linear(model.fc.in_features, 2)

# 🔹 Opción alternativa (MobileNetV2)
# model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
# model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)

# 🔹 Opción alternativa (EfficientNet-B0)
# model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
# model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)

model = model.to(device)

# =====================
# ENTRENAMIENTO
# =====================
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# GradScaler solo si hay CUDA
scaler = GradScaler(enabled=torch.cuda.is_available())

best_val_loss = float("inf")
early_stop_counter = 0
PATIENCE = 5

for epoch in range(NUM_EPOCHS):
    # -----------------
    # FASE DE TRAINING
    # -----------------
    model.train()
    running_loss, correct, total = 0.0, 0, 0

    train_loop = tqdm(train_loader, desc=f"Época {epoch+1}/{NUM_EPOCHS} [Entrenando]", leave=False)

    for images, labels in train_loop:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()

        with autocast(enabled=torch.cuda.is_available()):
            outputs = model(images)
            loss = criterion(outputs, labels)

        if device.type == "cuda":
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

        train_loop.set_postfix(loss=loss.item())

    train_loss = running_loss / len(train_loader.dataset)
    train_acc = 100 * correct / total

    # -----------------
    # FASE DE VALIDACIÓN
    # -----------------
    model.eval()
    val_loss, correct, total = 0.0, 0, 0

    val_loop = tqdm(val_loader, desc=f"Época {epoch+1}/{NUM_EPOCHS} [Validando]", leave=False)

    with torch.no_grad():
        for images, labels in val_loop:
            images, labels = images.to(device), labels.to(device)

            with autocast(enabled=torch.cuda.is_available()):
                outputs = model(images)
                loss = criterion(outputs, labels)

            val_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

            val_loop.set_postfix(loss=loss.item())

    val_loss /= len(val_loader.dataset)
    val_acc = 100 * correct / total

    print(f"\n📊 Época [{epoch+1}/{NUM_EPOCHS}] "
          f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
          f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")

    # Guardar mejor modelo
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), "best_model.pth")
        early_stop_counter = 0
    else:
        early_stop_counter += 1
        if early_stop_counter >= PATIENCE:
            print("⏹️ Early stopping activado. Entrenamiento detenido.")
            break

print("✅ Entrenamiento finalizado. Modelo guardado como best_model.pth")
