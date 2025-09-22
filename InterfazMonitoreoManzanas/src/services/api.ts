/**
 * Servicio de API para comunicación con el backend de detección de manzanas
 */

import { API_CONFIG, API_ENDPOINTS } from '../config/api';

const API_BASE_URL = API_CONFIG.BASE_URL;

export interface DetectionResult {
  timestamp: string;
  classification: string;
  confidence: number;
  is_fruit: boolean;
  fruit_type: string;
  spoiled: boolean;
  image_shape: number[];
  analysis_details: Record<string, any>;
  file_paths: {
    original: string;
    roi: string | null;
    mask: string | null;
  };
}

export interface StatsResponse {
  summary: {
    total_detections: number;
    total_fruits: number;
    total_non_fruits: number;
    fruits_by_type: Record<string, number>;
    fruits_by_status: {
      OK: number;
      MALOGRADA: number;
    };
    success_rate: number;
  };
  detection_history: Array<{
    timestamp: string;
    classification: string;
    confidence: number;
    is_fruit: boolean;
    fruit_type: string;
    spoiled: boolean;
    file_paths: {
      original: string;
      roi: string | null;
      mask: string | null;
    };
  }>;
  last_updated: string;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  timestamp: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Verificar estado del servicio
   */
  async checkHealth(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.HEALTH}`);
    if (!response.ok) {
      throw new Error(`Error checking health: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Procesar imagen y obtener resultado de detección
   */
  async detectFruit(imageFile: File): Promise<DetectionResult> {
    const formData = new FormData();
    formData.append('file', imageFile);

    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.DETECT}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error processing image: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Obtener estadísticas de detección
   */
  async getStats(): Promise<StatsResponse> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.STATS}`);
    if (!response.ok) {
      throw new Error(`Error getting stats: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Obtener historial de detecciones
   */
  async getDetectionHistory(limit: number = 50): Promise<{
    history: Array<any>;
    total: number;
  }> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.HISTORY}?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`Error getting history: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Resetear estadísticas
   */
  async resetStats(): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.STATS}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Error resetting stats: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Capturar y detectar desde cámara (simulado)
   */
  async captureAndDetect(): Promise<DetectionResult> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.CAPTURE}`, {
      method: 'POST',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error en captura: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Toggle modo live
   */
  async toggleLiveMode(): Promise<{ message: string; is_live: boolean; timestamp: string }> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.TOGGLE_LIVE}`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Error toggling live mode: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Iniciar cámara
   */
  async startCamera(): Promise<{ message: string; status: string }> {
    const response = await fetch(`${this.baseUrl}/camera/start`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Error iniciando cámara: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Detener cámara
   */
  async stopCamera(): Promise<{ message: string; status: string }> {
    const response = await fetch(`${this.baseUrl}/camera/stop`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Error deteniendo cámara: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Obtener estado de la cámara
   */
  async getCameraStatus(): Promise<{
    is_running: boolean;
    is_live: boolean;
    frame_count: number;
    has_latest_frame: boolean;
    has_latest_result: boolean;
  }> {
    const response = await fetch(`${this.baseUrl}/camera/status`);

    if (!response.ok) {
      throw new Error(`Error obteniendo estado de cámara: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Obtener URL de imagen procesada
   */
  getImageUrl(filePath: string): string {
    // Convertir ruta del servidor a URL accesible
    const relativePath = filePath.replace(/\\/g, '/').replace('salidas/', '');
    return `${this.baseUrl}/static/${relativePath}`;
  }
}

// Instancia singleton del servicio
export const apiService = new ApiService();

// Hook personalizado para usar el servicio de API
export const useApi = () => {
  return {
    checkHealth: () => apiService.checkHealth(),
    detectFruit: (file: File) => apiService.detectFruit(file),
    getStats: () => apiService.getStats(),
    getDetectionHistory: (limit?: number) => apiService.getDetectionHistory(limit),
    resetStats: () => apiService.resetStats(),
    captureAndDetect: () => apiService.captureAndDetect(),
    toggleLiveMode: () => apiService.toggleLiveMode(),
    startCamera: () => apiService.startCamera(),
    stopCamera: () => apiService.stopCamera(),
    getCameraStatus: () => apiService.getCameraStatus(),
    getImageUrl: (filePath: string) => apiService.getImageUrl(filePath),
  };
};
