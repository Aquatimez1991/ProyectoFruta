import React, { useState, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Upload, Image as ImageIcon, X, CheckCircle, AlertCircle } from 'lucide-react';
import { apiService, DetectionResult } from '../services/api';

interface ImageUploadProps {
  onDetectionResult: (result: DetectionResult) => void;
  onError: (error: string) => void;
  disabled?: boolean;
}

export function ImageUpload({ onDetectionResult, onError, disabled = false }: ImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    // Validar tipo de archivo
    if (!file.type.startsWith('image/')) {
      onError('Por favor selecciona un archivo de imagen válido');
      return;
    }

    // Validar tamaño (máximo 10MB)
    if (file.size > 10 * 1024 * 1024) {
      onError('El archivo es demasiado grande. Máximo 10MB');
      return;
    }

    setSelectedFile(file);
    
    // Crear preview
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    
    const file = event.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    try {
      const result = await apiService.detectFruit(selectedFile);
      onDetectionResult(result);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Error procesando la imagen');
    } finally {
      setIsUploading(false);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Subir Imagen
        </CardTitle>
        <CardDescription>
          Selecciona una imagen de manzana para analizar su estado
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Área de drop */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={openFileDialog}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileInputChange}
            className="hidden"
            disabled={disabled}
          />
          
          {previewUrl ? (
            <div className="space-y-4">
              <img
                src={previewUrl}
                alt="Preview"
                className="max-h-48 mx-auto rounded-lg shadow-sm"
              />
              <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
                <CheckCircle className="h-4 w-4 text-green-500" />
                {selectedFile?.name}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <ImageIcon className="h-12 w-12 mx-auto text-gray-400" />
              <div>
                <p className="text-lg font-medium text-gray-700">
                  Arrastra una imagen aquí o haz clic para seleccionar
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Formatos soportados: JPG, PNG, GIF (máximo 10MB)
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Botones de acción */}
        {selectedFile && (
          <div className="flex gap-2">
            <Button
              onClick={handleUpload}
              disabled={isUploading || disabled}
              className="flex-1"
            >
              {isUploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Procesando...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Analizar Imagen
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={clearFile}
              disabled={isUploading || disabled}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Información adicional */}
        <div className="text-xs text-gray-500 space-y-1">
          <p>• La imagen será procesada usando el modelo de IA entrenado</p>
          <p>• Se detectará automáticamente si hay una manzana en la imagen</p>
          <p>• Se clasificará como "buena" o "mala" según su estado</p>
        </div>
      </CardContent>
    </Card>
  );
}
