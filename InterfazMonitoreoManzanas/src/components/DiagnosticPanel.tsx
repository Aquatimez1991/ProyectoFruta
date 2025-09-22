import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { apiService } from '../services/api';

interface DiagnosticResult {
  endpoint: string;
  status: 'success' | 'error' | 'pending';
  message: string;
  response?: any;
}

export function DiagnosticPanel() {
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const runDiagnostics = async () => {
    setIsRunning(true);
    setResults([]);

    const endpoints = [
      { name: 'Health Check', url: '/health', method: 'GET' },
      { name: 'Test Endpoint', url: '/test', method: 'GET' },
      { name: 'Stats', url: '/stats', method: 'GET' },
      { name: 'History', url: '/history', method: 'GET' },
      { name: 'Toggle Live', url: '/toggle_live', method: 'POST' },
      { name: 'Capture', url: '/capture', method: 'POST' },
    ];

    const newResults: DiagnosticResult[] = [];

    for (const endpoint of endpoints) {
      const result: DiagnosticResult = {
        endpoint: `${endpoint.method} ${endpoint.url}`,
        status: 'pending',
        message: 'Probando...'
      };
      
      setResults([...newResults, result]);
      newResults.push(result);

      try {
        let response;
        if (endpoint.method === 'GET') {
          response = await fetch(`http://localhost:8000${endpoint.url}`);
        } else {
          response = await fetch(`http://localhost:8000${endpoint.url}`, {
            method: 'POST'
          });
        }

        if (response.ok) {
          const data = await response.json();
          result.status = 'success';
          result.message = `✅ OK (${response.status})`;
          result.response = data;
        } else {
          result.status = 'error';
          result.message = `❌ Error ${response.status}: ${response.statusText}`;
        }
      } catch (error) {
        result.status = 'error';
        result.message = `❌ Error: ${error instanceof Error ? error.message : 'Desconocido'}`;
      }

      setResults([...newResults]);
    }

    setIsRunning(false);
  };

  const getStatusIcon = (status: DiagnosticResult['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
    }
  };

  const getStatusBadge = (status: DiagnosticResult['status']) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-100 text-green-800">OK</Badge>;
      case 'error':
        return <Badge className="bg-red-100 text-red-800">Error</Badge>;
      case 'pending':
        return <Badge className="bg-blue-100 text-blue-800">Probando</Badge>;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          Diagnóstico de API
        </CardTitle>
        <CardDescription>
          Verifica el estado de todos los endpoints del backend
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button 
          onClick={runDiagnostics} 
          disabled={isRunning}
          className="w-full"
        >
          {isRunning ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Ejecutando diagnóstico...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4 mr-2" />
              Ejecutar Diagnóstico
            </>
          )}
        </Button>

        {results.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium">Resultados:</h4>
            {results.map((result, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(result.status)}
                  <div>
                    <p className="font-mono text-sm">{result.endpoint}</p>
                    <p className="text-xs text-gray-600">{result.message}</p>
                  </div>
                </div>
                {getStatusBadge(result.status)}
              </div>
            ))}
          </div>
        )}

        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>Instrucciones:</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• Asegúrate de que el backend esté ejecutándose</li>
              <li>• Verifica que no haya errores en la consola del backend</li>
              <li>• Si algún endpoint falla, reinicia el backend</li>
              <li>• Usa <code>restart_backend.bat</code> para reiniciar automáticamente</li>
            </ul>
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}
