import { ImageWithFallback } from "./figma/ImageWithFallback";
import { DetectionResult, apiService } from "../services/api";
import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { RotateCcw, Trash2 } from "lucide-react";

interface CameraPanelProps {
  isProcessing: boolean;
  lastClassification: string | null;
  detectionResult?: DetectionResult | null;
  backendConnected?: boolean;
  isStreaming?: boolean;
  onStartStreaming?: () => void;
  onStopStreaming?: () => void;
  onStatsReset?: () => void;
}

export function CameraPanel({ 
  isProcessing, 
  lastClassification, 
  detectionResult,
  backendConnected = false,
  isStreaming = false,
  onStartStreaming,
  onStopStreaming,
  onStatsReset
}: CameraPanelProps) {
  const [latestImageUrl, setLatestImageUrl] = useState<string | null>(null);
  const [isResetting, setIsResetting] = useState(false);

  // Actualizar imagen cuando hay un nuevo resultado
  useEffect(() => {
    if (detectionResult && backendConnected) {
      // Intentar obtener la imagen más reciente del backend
      const imageUrl = `http://localhost:8000/latest_image?t=${Date.now()}`;
      setLatestImageUrl(imageUrl);
    }
  }, [detectionResult, backendConnected]);

  const handleResetStats = async () => {
    if (!backendConnected) return;
    
    setIsResetting(true);
    try {
      await apiService.resetStats();
      console.log('✅ Estadísticas reseteadas correctamente');
      if (onStatsReset) {
        onStatsReset();
      }
    } catch (error) {
      console.error('❌ Error reseteando estadísticas:', error);
    } finally {
      setIsResetting(false);
    }
  };

  const getStatusText = () => {
    if (isProcessing) return "Reconociendo...";
    if (detectionResult) {
      if (detectionResult.is_fruit) {
        return `Clasificada: ${detectionResult.classification} (${(detectionResult.confidence * 100).toFixed(1)}%)`;
      } else {
        return "No se detectó fruta";
      }
    }
    if (lastClassification) return `Clasificada: ${lastClassification}`;
    return "En espera";
  };

  const getStatusColor = () => {
    if (isProcessing) return "text-yellow-600";
    if (detectionResult) {
      if (!detectionResult.is_fruit) return "text-gray-600";
      return detectionResult.spoiled ? "text-red-600" : "text-emerald-600";
    }
    if (lastClassification === "BUENA") return "text-emerald-600";
    if (lastClassification === "MALA") return "text-red-600";
    return "text-gray-600";
  };

  const getImageSource = () => {
    // Si está en modo streaming, usar el stream de video
    if (isStreaming && backendConnected) {
      return "http://localhost:8000/video_stream";
    }
    // Si hay una imagen del backend, usarla
    if (latestImageUrl && backendConnected) {
      return latestImageUrl;
    }
    // Imagen por defecto
    return "https://images.unsplash.com/photo-1623815242959-fb20354f9b8d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMHJlZCUyMGFwcGxlJTIwZnJ1aXR8ZW58MXx8fHwxNzU4NTYxMTIyfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral";
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg text-gray-800">Vista de Cámara en Tiempo Real</h3>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${backendConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-xs text-gray-600">
              {backendConnected ? 'Backend conectado' : 'Backend desconectado'}
            </span>
            {isStreaming && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                <span className="text-xs text-blue-600">Streaming</span>
              </div>
            )}
          </div>
          
          {backendConnected && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetStats}
              disabled={isResetting}
              className="flex items-center gap-1 text-xs"
            >
              <Trash2 className="w-3 h-3" />
              {isResetting ? 'Reseteando...' : 'Reset Stats'}
            </Button>
          )}
        </div>
      </div>
      
      <div className="relative">
        <div className="bg-gray-900 rounded-lg p-4 border-4 border-slate-700">
          <div className="aspect-video bg-gray-800 rounded-lg overflow-hidden flex items-center justify-center">
            {isStreaming ? (
              <img
                src={getImageSource()}
                alt="Stream de cámara en tiempo real"
                className="w-full h-full object-cover"
                style={{ imageRendering: 'auto' }}
              />
            ) : (
              <ImageWithFallback
                src={getImageSource()}
                alt="Manzana detectada"
                className="w-full h-full object-cover"
              />
            )}
          </div>
        </div>
        
        {isProcessing && (
          <div className="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center">
            <div className="bg-white px-4 py-2 rounded-lg flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-gray-800">
                {backendConnected ? 'Procesando con IA...' : 'Procesando...'}
              </span>
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Estado:</span>
          <span className={`font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>
      </div>

      {/* Información del backend si está disponible */}
      {detectionResult && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="text-sm font-medium text-blue-800 mb-2">Información del Backend</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-blue-600">Tipo:</span>
              <span className="ml-1 text-blue-800">{detectionResult.fruit_type}</span>
            </div>
            <div>
              <span className="text-blue-600">Confianza:</span>
              <span className="ml-1 text-blue-800">{(detectionResult.confidence * 100).toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-blue-600">Dimensiones:</span>
              <span className="ml-1 text-blue-800">
                {detectionResult.image_shape[1]}×{detectionResult.image_shape[0]}
              </span>
            </div>
            <div>
              <span className="text-blue-600">Timestamp:</span>
              <span className="ml-1 text-blue-800">{detectionResult.timestamp}</span>
            </div>
          </div>
        </div>
      )}
      
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="text-blue-600">Resolución</div>
          <div className="text-blue-800">
            {detectionResult ? 
              `${detectionResult.image_shape[1]}×${detectionResult.image_shape[0]}` : 
              '1920x1080'
            }
          </div>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <div className="text-purple-600">Modo</div>
          <div className="text-purple-800">
            {backendConnected ? 'IA Real' : 'Simulación'}
          </div>
        </div>
      </div>
    </div>
  );
}