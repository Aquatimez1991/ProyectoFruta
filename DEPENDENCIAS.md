# DEPENDENCIAS DEL PROYECTO

Este documento describe las dependencias principales utilizadas en el proyecto "Visión Artificial para el Control de Calidad en la Industria Alimentaria".

---

## Backend (Python/FastAPI)

- **fastapi**: Framework para crear la API REST del backend.
- **uvicorn[standard]**: Servidor ASGI para ejecutar aplicaciones FastAPI.
- **python-multipart**: Manejo de archivos subidos (imágenes) en endpoints FastAPI.
- **opencv-python**: Procesamiento de imágenes, segmentación y extracción de características.
- **onnxruntime**: Inferencia de modelos ONNX para clasificación de frutas.
- **numpy**: Operaciones numéricas y manejo de arrays en procesamiento de imágenes y datos.
- **Pillow**: Manipulación de imágenes (carga, guardado, conversión entre formatos).
- **python-jose[cryptography]**: Autenticación y manejo de tokens JWT (si se usa seguridad en la API).
- **passlib[bcrypt]**: Hashing de contraseñas para autenticación de usuarios.
- **python-dotenv**: Carga de variables de entorno desde archivos .env.
- **pydantic**: Validación y tipado de datos en FastAPI (modelos de entrada/salida).
- **aiofiles**: Lectura/escritura asíncrona de archivos (usado en FastAPI para manejar imágenes).
- **torch**: Framework de deep learning para entrenamiento y manejo de modelos de clasificación.
- **torchvision**: Utilidades para procesamiento de imágenes y modelos preentrenados en PyTorch.

---

## Frontend (React/Vite)

- **@radix-ui/react-***: Componentes UI modernos y accesibles (acordeón, diálogos, menús, pestañas, tooltips, etc.).
- **class-variance-authority**: Utilidad para manejar variantes de clases CSS de forma dinámica.
- **clsx**: Combina y gestiona clases CSS condicionalmente.
- **cmdk**: Implementa un "Command Palette" (buscador rápido de acciones).
- **embla-carousel-react**: Carrusel de imágenes, útil para mostrar resultados o ejemplos.
- **input-otp**: Inputs para códigos OTP (autenticación o validación).
- **lucide-react**: Iconos SVG modernos y personalizables.
- **next-themes**: Gestión de temas (oscuro/claro) en la interfaz.
- **react**: Librería principal para construir interfaces de usuario.
- **react-day-picker**: Selector de fechas.
- **react-dom**: Renderizado de componentes React en el DOM.
- **react-hook-form**: Manejo eficiente y reactivo de formularios.
- **react-resizable-panels**: Paneles redimensionables para layouts flexibles.
- **recharts**: Gráficas y visualización de datos estadísticos.
- **sonner**: Notificaciones y toasts para feedback al usuario.
- **tailwind-merge**: Utilidad para combinar clases de Tailwind CSS.
- **vaul**: Componentes UI adicionales.
- **@types/node**, **@types/react**, **@types/react-dom**: Tipos para TypeScript, mejorando el autocompletado y la validación.
- **@vitejs/plugin-react-swc**: Compilador rápido para React con Vite.
- **vite**: Bundler y servidor de desarrollo ultrarrápido.

---

## Recomendaciones

- Mantén este archivo actualizado al agregar o eliminar dependencias.
- Documenta dependencias especiales o personalizadas.
- Agrega ejemplos de uso si es relevante.

---

# ENDPOINTS PRINCIPALES DE LA API (FastAPI)

## POST /api/detectar
- **Descripción:** Recibe una imagen y devuelve la clasificación, tipo de fruta y estadísticas.
- **Body:** FormData con campo 'file' (imagen)
- **Respuesta:** JSON con resultado de clasificación, tipo de fruta, confianza y metadatos.

## GET /api/estadisticas
- **Descripción:** Devuelve estadísticas históricas de detección y clasificación.
- **Respuesta:** JSON con totales, porcentajes y registros.

## GET /api/capturas
- **Descripción:** Lista las capturas almacenadas y sus metadatos.
- **Respuesta:** JSON con rutas de archivos y detalles.

## Otros endpoints
- **Configuración:** Endpoints para consultar y modificar parámetros del sistema (umbral, resolución, FPS, etc.)
- **Autenticación:** Si se usa, endpoints para login y gestión de usuarios.

---

## Ejemplo de flujo de integración

1. El usuario selecciona una fruta y captura una imagen desde el frontend.
2. La imagen se envía al backend vía POST `/api/detectar`.
3. El backend procesa la imagen, ejecuta la inferencia y responde con la clasificación y tipo de fruta.
4. El frontend muestra el resultado y actualiza las estadísticas.

---


---

## Consumo de la API desde React (Frontend)

El frontend se comunica con el backend mediante peticiones HTTP a la API REST de FastAPI. A continuación se muestra un ejemplo de cómo consumir el endpoint de detección desde React usando `fetch`:

```typescript
// Ejemplo: Enviar imagen al backend y recibir resultado
async function detectarFruta(file: File): Promise<any> {
	const formData = new FormData();
	formData.append('file', file);
	const response = await fetch('http://localhost:8000/api/detectar', {
		method: 'POST',
		body: formData
	});
	if (!response.ok) throw new Error('Error en la detección');
	return await response.json();
}

// Uso en un componente React
const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
	if (event.target.files && event.target.files[0]) {
		try {
			const resultado = await detectarFruta(event.target.files[0]);
			// Actualizar estado con resultado
			setResultado(resultado);
		} catch (error) {
			// Manejar error
		}
	}
};
```

### Integración con el backend

- El frontend envía imágenes y recibe resultados de clasificación, tipo de fruta y estadísticas.
- Los resultados se muestran en tiempo real en la interfaz, junto con gráficas y notificaciones.
- Se pueden consultar estadísticas y capturas históricas mediante peticiones GET a los endpoints correspondientes.
- La configuración del sistema (umbral, resolución, etc.) puede gestionarse desde la interfaz y enviarse al backend si existen endpoints para ello.

**Recomendaciones:**
- Usar variables de entorno para la URL del backend (`REACT_APP_API_URL`).
- Manejar errores y estados de carga en la interfaz.
- Validar los datos recibidos antes de mostrarlos.

---
