#!/usr/bin/env python3
"""
Script de prueba para la API de detección de manzanas
"""
import requests
import json
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_health():
    """Probar endpoint de salud"""
    print("🔍 Probando endpoint de salud...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend saludable: {data['status']}")
            print(f"   Modelo cargado: {data['model_loaded']}")
            return True
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al backend. ¿Está ejecutándose?")
        return False

def test_detection(image_path):
    """Probar detección con una imagen"""
    print(f"🔍 Probando detección con imagen: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"❌ Imagen no encontrada: {image_path}")
        return False
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_BASE_URL}/detect", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Detección exitosa:")
            print(f"   Clasificación: {data['classification']}")
            print(f"   Confianza: {data['confidence']:.2f}")
            print(f"   Es fruta: {data['is_fruit']}")
            print(f"   Tipo: {data['fruit_type']}")
            print(f"   Malograda: {data['spoiled']}")
            return True
        else:
            print(f"❌ Error en detección: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error procesando imagen: {e}")
        return False

def test_stats():
    """Probar endpoint de estadísticas"""
    print("🔍 Probando endpoint de estadísticas...")
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Estadísticas obtenidas:")
            summary = data['summary']
            print(f"   Total detecciones: {summary['total_detections']}")
            print(f"   Total frutas: {summary['total_fruits']}")
            print(f"   Total no frutas: {summary['total_non_fruits']}")
            print(f"   Tasa de éxito: {summary['success_rate']:.2f}")
            return True
        else:
            print(f"❌ Error obteniendo estadísticas: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_history():
    """Probar endpoint de historial"""
    print("🔍 Probando endpoint de historial...")
    try:
        response = requests.get(f"{API_BASE_URL}/history?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Historial obtenido: {data['total']} entradas")
            if data['history']:
                print("   Últimas detecciones:")
                for entry in data['history'][-3:]:
                    print(f"     - {entry['timestamp']}: {entry['classification']} ({entry['confidence']:.2f})")
            return True
        else:
            print(f"❌ Error obteniendo historial: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🧪 Iniciando pruebas de la API de detección de manzanas")
    print("=" * 60)
    
    # Probar salud del backend
    if not test_health():
        print("\n❌ Backend no disponible. Terminando pruebas.")
        return
    
    print()
    
    # Probar estadísticas
    test_stats()
    print()
    
    # Probar historial
    test_history()
    print()
    
    # Buscar imágenes de prueba
    test_images = []
    
    # Buscar en el directorio actual
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif']:
        test_images.extend(Path('.').glob(ext))
        test_images.extend(Path('ProyectoFruta').glob(ext))
    
    if test_images:
        print(f"📸 Imágenes de prueba encontradas: {len(test_images)}")
        for img in test_images[:3]:  # Probar máximo 3 imágenes
            test_detection(str(img))
            print()
    else:
        print("⚠️  No se encontraron imágenes de prueba")
        print("   Coloca algunas imágenes .jpg/.png en el directorio para probar la detección")
    
    print("=" * 60)
    print("✅ Pruebas completadas")

if __name__ == "__main__":
    main()
