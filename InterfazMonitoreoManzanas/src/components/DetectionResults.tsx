import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Image as ImageIcon,
  Target,
  BarChart3,
  Clock
} from 'lucide-react';
import { DetectionResult } from '../services/api';

interface DetectionResultsProps {
  result: DetectionResult;
  onClose?: () => void;
}

export function DetectionResults({ result, onClose }: DetectionResultsProps) {
  const getClassificationIcon = () => {
    if (!result.is_fruit) {
      return <XCircle className="h-5 w-5 text-gray-500" />;
    }
    return result.spoiled ? 
      <XCircle className="h-5 w-5 text-red-500" /> : 
      <CheckCircle className="h-5 w-5 text-green-500" />;
  };

  const getClassificationColor = () => {
    if (!result.is_fruit) {
      return 'bg-gray-100 text-gray-800';
    }
    return result.spoiled ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800';
  };

  const getClassificationText = () => {
    if (!result.is_fruit) {
      return 'No se detectó fruta';
    }
    return result.spoiled ? 'Manzana en mal estado' : 'Manzana en buen estado';
  };

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(1)}%`;
  };

  const formatTimestamp = (timestamp: string) => {
    // Convertir timestamp YYYYMMDD_HHMMSS a formato legible
    const year = timestamp.substring(0, 4);
    const month = timestamp.substring(4, 6);
    const day = timestamp.substring(6, 8);
    const hour = timestamp.substring(9, 11);
    const minute = timestamp.substring(11, 13);
    const second = timestamp.substring(13, 15);
    
    return `${day}/${month}/${year} ${hour}:${minute}:${second}`;
  };

  return (
    <div className="space-y-4">
      {/* Resultado principal */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getClassificationIcon()}
            Resultado del Análisis
          </CardTitle>
          <CardDescription>
            Análisis completado el {formatTimestamp(result.timestamp)}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Clasificación principal */}
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Clasificación</h3>
              <p className="text-sm text-gray-600">{result.classification}</p>
            </div>
            <Badge className={`px-3 py-1 ${getClassificationColor()}`}>
              {getClassificationText()}
            </Badge>
          </div>

          {/* Confianza */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">Confianza</span>
            </div>
            <span className="text-sm font-mono">{formatConfidence(result.confidence)}</span>
          </div>

          {/* Tipo de fruta */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-purple-500" />
              <span className="text-sm font-medium">Tipo de fruta</span>
            </div>
            <span className="text-sm">{result.fruit_type}</span>
          </div>

          {/* Dimensiones de la imagen */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ImageIcon className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">Dimensiones</span>
            </div>
            <span className="text-sm font-mono">
              {result.image_shape[1]} × {result.image_shape[0]} px
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Alertas o detalles adicionales */}
      {Object.keys(result.analysis_details).length > 0 && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {Object.entries(result.analysis_details).map(([key, value]) => (
              <div key={key}>
                <strong>{key}:</strong> {String(value)}
              </div>
            ))}
          </AlertDescription>
        </Alert>
      )}

      {/* Información técnica */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Información Técnica</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs text-gray-600">
          <div className="flex justify-between">
            <span>Timestamp:</span>
            <span className="font-mono">{result.timestamp}</span>
          </div>
          <div className="flex justify-between">
            <span>Es fruta:</span>
            <span>{result.is_fruit ? 'Sí' : 'No'}</span>
          </div>
          <div className="flex justify-between">
            <span>Estado:</span>
            <span>{result.spoiled ? 'Malograda' : 'Buena'}</span>
          </div>
          {result.file_paths.roi && (
            <div className="flex justify-between">
              <span>ROI detectada:</span>
              <span>Sí</span>
            </div>
          )}
          {result.file_paths.mask && (
            <div className="flex justify-between">
              <span>Máscara generada:</span>
              <span>Sí</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Archivos generados */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Archivos Generados</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-600">Imagen original:</span>
              <span className="font-mono text-xs truncate max-w-48">
                {result.file_paths.original.split('/').pop()}
              </span>
            </div>
            {result.file_paths.roi && (
              <div className="flex justify-between">
                <span className="text-gray-600">ROI extraída:</span>
                <span className="font-mono text-xs truncate max-w-48">
                  {result.file_paths.roi.split('/').pop()}
                </span>
              </div>
            )}
            {result.file_paths.mask && (
              <div className="flex justify-between">
                <span className="text-gray-600">Máscara:</span>
                <span className="font-mono text-xs truncate max-w-48">
                  {result.file_paths.mask.split('/').pop()}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
