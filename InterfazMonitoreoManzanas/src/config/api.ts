/**
 * Configuración de la API
 */

// URL base del backend - cambiar según sea necesario
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000',
  TIMEOUT: 30000, // 30 segundos
  RETRY_ATTEMPTS: 3,
};

// Endpoints de la API
export const API_ENDPOINTS = {
  HEALTH: '/health',
  DETECT: '/detect',
  STATS: '/stats',
  HISTORY: '/history',
  CAPTURE: '/capture',
  TOGGLE_LIVE: '/toggle_live',
} as const;

// Configuración de CORS
export const CORS_CONFIG = {
  ALLOWED_ORIGINS: [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
  ],
};

// Configuración de archivos
export const FILE_CONFIG = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'],
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.gif'],
};

// Configuración de la aplicación
export const APP_CONFIG = {
  NAME: 'Sistema de Detección de Manzanas',
  VERSION: '1.0.0',
  DESCRIPTION: 'Sistema de detección y clasificación de manzanas usando IA',
};
