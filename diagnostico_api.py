#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la API
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_all_endpoints():
    """Probar todos los endpoints disponibles"""
    endpoints = [
        ("GET", "/health"),
        ("GET", "/test"),
        ("GET", "/stats"),
        ("GET", "/history"),
        ("POST", "/toggle_live"),
        ("POST", "/capture"),
    ]
    
    print("🔍 Probando todos los endpoints...")
    print("=" * 50)
    
    for method, endpoint in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        print(f"\n{method} {endpoint}")
        print(f"URL: {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"Response: {response.text}")
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Error de conexión - Backend no disponible")
        except requests.exceptions.Timeout:
            print("❌ Timeout - Backend no responde")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_cors():
    """Probar configuración CORS"""
    print("\n🔗 Probando CORS...")
    print("=" * 30)
    
    headers = {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
    }
    
    try:
        response = requests.options(f"{API_BASE_URL}/toggle_live", headers=headers)
        print(f"OPTIONS /toggle_live: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"Error CORS: {e}")

def main():
    print("🧪 DIAGNÓSTICO DE LA API")
    print("=" * 50)
    
    # Probar conexión básica
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        print(f"✅ Backend disponible en {API_BASE_URL}")
        print(f"   Status: {response.status_code}")
    except:
        print(f"❌ Backend NO disponible en {API_BASE_URL}")
        print("   Asegúrate de que esté ejecutándose con: python app.py")
        return
    
    # Probar todos los endpoints
    test_all_endpoints()
    
    # Probar CORS
    test_cors()
    
    print("\n" + "=" * 50)
    print("💡 INSTRUCCIONES:")
    print("1. Si algún endpoint falla, reinicia el backend")
    print("2. Verifica que no haya errores en la consola del backend")
    print("3. Asegúrate de que el puerto 8000 esté libre")

if __name__ == "__main__":
    main()
