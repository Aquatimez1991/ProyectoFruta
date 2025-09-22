#!/usr/bin/env python3
"""
Script de prueba para verificar la integración completa del sistema
"""
import requests
import json
import os
import time
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_backend_connection():
    """Probar conexión con el backend"""
    print("🔍 Probando conexión con el backend...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend conectado: {data['status']}")
            print(f"   Modelo cargado: {data['model_loaded']}")
            return True
        else:
            print(f"❌ Error en conexión: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al backend")
        print("   Asegúrate de que el backend esté ejecutándose en http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_camera_endpoints():
    """Probar endpoints de cámara"""
    print("\n📸 Probando endpoints de cámara...")
    
    # Probar toggle live
    try:
        response = requests.post(f"{API_BASE_URL}/toggle_live")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Toggle live: {data['message']}")
        else:
            print(f"❌ Error en toggle live: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en toggle live: {e}")
    
    # Probar captura
    try:
        response = requests.post(f"{API_BASE_URL}/capture")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Captura exitosa:")
            print(f"   Clasificación: {data['classification']}")
            print(f"   Confianza: {data['confidence']:.2f}")
            print(f"   Es fruta: {data['is_fruit']}")
            return True
        else:
            print(f"❌ Error en captura: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error en captura: {e}")
        return False

def test_frontend_connection():
    """Probar si el frontend está ejecutándose"""
    print("\n🌐 Probando conexión con el frontend...")
    frontend_urls = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000"
    ]
    
    for url in frontend_urls:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ Frontend detectado en: {url}")
                return url
        except:
            continue
    
    print("⚠️  Frontend no detectado en los puertos comunes")
    print("   Asegúrate de que el frontend esté ejecutándose")
    return None

def test_cors_configuration():
    """Probar configuración CORS"""
    print("\n🔗 Probando configuración CORS...")
    
    # Simular request desde frontend
    headers = {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
    }
    
    try:
        response = requests.options(f"{API_BASE_URL}/detect", headers=headers)
        if response.status_code == 200:
            cors_headers = response.headers
            print("✅ CORS configurado correctamente")
            if 'Access-Control-Allow-Origin' in cors_headers:
                print(f"   Origen permitido: {cors_headers['Access-Control-Allow-Origin']}")
            return True
        else:
            print(f"❌ Error en CORS: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error probando CORS: {e}")
        return False

def test_image_processing():
    """Probar procesamiento de imagen"""
    print("\n🖼️  Probando procesamiento de imagen...")
    
    # Buscar imágenes de prueba
    test_images = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        test_images.extend(Path('ProyectoFruta').glob(ext))
    
    if not test_images:
        print("⚠️  No se encontraron imágenes de prueba en ProyectoFruta/")
        return False
    
    image_path = test_images[0]
    print(f"   Usando imagen: {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_BASE_URL}/detect", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Procesamiento exitoso:")
            print(f"   Clasificación: {data['classification']}")
            print(f"   Confianza: {data['confidence']:.2f}")
            print(f"   Es fruta: {data['is_fruit']}")
            print(f"   Tipo: {data['fruit_type']}")
            return True
        else:
            print(f"❌ Error en procesamiento: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error procesando imagen: {e}")
        return False

def main():
    print("🧪 Prueba de Integración Completa del Sistema")
    print("=" * 60)
    
    # Probar conexión backend
    backend_ok = test_backend_connection()
    if not backend_ok:
        print("\n❌ Backend no disponible. Terminando pruebas.")
        return
    
    # Probar endpoints de cámara
    camera_ok = test_camera_endpoints()
    
    # Probar frontend
    frontend_url = test_frontend_connection()
    
    # Probar CORS
    cors_ok = test_cors_configuration()
    
    # Probar procesamiento de imagen
    image_ok = test_image_processing()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"   Backend: {'✅ OK' if backend_ok else '❌ FALLO'}")
    print(f"   Cámara: {'✅ OK' if camera_ok else '❌ FALLO'}")
    print(f"   Frontend: {'✅ OK' if frontend_url else '❌ FALLO'}")
    print(f"   CORS: {'✅ OK' if cors_ok else '❌ FALLO'}")
    print(f"   Imagen: {'✅ OK' if image_ok else '❌ FALLO'}")
    
    if backend_ok and camera_ok and frontend_url and cors_ok and image_ok:
        print("\n🎉 ¡Todas las pruebas pasaron! El sistema está listo para usar.")
        print(f"   Frontend: {frontend_url}")
        print("   Backend: http://localhost:8000")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa la configuración.")
    
    print("\n💡 INSTRUCCIONES:")
    print("   1. Asegúrate de que ambos servicios estén ejecutándose")
    print("   2. Abre el frontend en tu navegador")
    print("   3. Ve a la pestaña 'Subir Imagen' para probar detección")
    print("   4. Ve a la pestaña 'Cámara' para probar funciones LIVE/CAPTURAR")

if __name__ == "__main__":
    main()
