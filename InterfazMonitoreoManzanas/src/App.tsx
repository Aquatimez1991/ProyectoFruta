import { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { ClassificationPanel } from "./components/ClassificationPanel";
import { CameraPanel } from "./components/CameraPanel";
import { BottomActions } from "./components/BottomActions";
import { SettingsPanel } from "./components/SettingsPanel";
import { HomePanel } from "./components/HomePanel";
import { StatsPanel } from "./components/StatsPanel";
import { ImageUpload } from "./components/ImageUpload";
import { DetectionResults } from "./components/DetectionResults";
import { apiService, DetectionResult, StatsResponse } from "./services/api";

export default function App() {
  const [activeTab, setActiveTab] = useState("home");
  const [goodCount, setGoodCount] = useState(0);
  const [badCount, setBadCount] = useState(0);
  const [isLive, setIsLive] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastClassification, setLastClassification] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [selectedFruit, setSelectedFruit] = useState("apple");
  
  // Estados para clasificación automática
  const [autoClassification, setAutoClassification] = useState<string | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [isAwaitingConfirmation, setIsAwaitingConfirmation] = useState(false);

  // Estados para integración con backend
  const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

  // Verificar conexión con backend al cargar
  useEffect(() => {
    checkBackendConnection();
    loadStats();
  }, []);

  const checkBackendConnection = async () => {
    try {
      const health = await apiService.checkHealth();
      setBackendConnected(health.model_loaded);
      setError(null);
    } catch (err) {
      setBackendConnected(false);
      setError('No se pudo conectar con el backend. Asegúrate de que esté ejecutándose en http://localhost:8000');
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await apiService.getStats();
      setStats(statsData);
      setGoodCount(statsData.summary.fruits_by_status.OK);
      setBadCount(statsData.summary.fruits_by_status.MALOGRADA);
    } catch (err) {
      console.error('Error cargando estadísticas:', err);
    }
  };

  const handleDetectionResult = (result: DetectionResult) => {
    setDetectionResult(result);
    setError(null);
    
    // Actualizar contadores basados en el resultado
    if (result.is_fruit) {
      if (result.spoiled) {
        setBadCount(prev => prev + 1);
        setLastClassification('MALA');
      } else {
        setGoodCount(prev => prev + 1);
        setLastClassification('BUENA');
      }
    }
    
    // Recargar estadísticas
    loadStats();
  };

  const handleApiError = (errorMessage: string) => {
    setError(errorMessage);
    setDetectionResult(null);
  };

  const simulateAutoClassification = () => {
    setIsProcessing(true);
    
    setTimeout(() => {
      const isGood = Math.random() > 0.3; // 70% probabilidad de ser buena
      const classification = isGood ? 'BUENA' : 'MALA';
      const confidenceLevel = Math.floor(Math.random() * 20) + 80; // 80-99%
      
      setAutoClassification(classification);
      setConfidence(confidenceLevel);
      setIsAwaitingConfirmation(true);
      setIsProcessing(false);
      setLastClassification(classification);
    }, 2000);
  };

  const handleClassify = (type: 'good' | 'bad') => {
    if (type === 'good') {
      setGoodCount(prev => prev + 1);
      setLastClassification('BUENA');
    } else {
      setBadCount(prev => prev + 1);
      setLastClassification('MALA');
    }
    
    // Resetear estado de confirmación
    setAutoClassification(null);
    setIsAwaitingConfirmation(false);
  };

  const handleCorrectClassification = () => {
    const correctedType = autoClassification === 'BUENA' ? 'bad' : 'good';
    handleClassify(correctedType);
    
    // Actualizar la clasificación automática mostrada
    setAutoClassification(autoClassification === 'BUENA' ? 'MALA' : 'BUENA');
  };

  const handleConfirmClassification = () => {
    const type = autoClassification === 'BUENA' ? 'good' : 'bad';
    handleClassify(type);
  };

  const handleToggleLive = () => {
    setIsLive(!isLive);
    if (!isLive) {
      // Simular clasificación automática cuando se activa LIVE
      setTimeout(simulateAutoClassification, 3000);
    }
  };

  const handleStartMonitoring = () => {
    setActiveTab("camera");
    setIsLive(true);
    setShowStats(false);
    setShowSettings(false);
    
    // Activar modo de monitoreo automático completo
    setTimeout(simulateAutoClassification, 3000);
  };

  const handleExit = () => {
    setActiveTab("home");
    setIsLive(false);
    setShowStats(false);
    setAutoClassification(null);
    setIsAwaitingConfirmation(false);
  };

  const handleCapture = () => {
    if (isLive) {
      simulateAutoClassification();
    }
  };

  const handleShowStats = () => {
    setShowStats(true);
    setActiveTab("stats");
  };

  const handleSelectFruit = (fruitId: string) => {
    setSelectedFruit(fruitId);
  };

  // Manejar cambio de pestaña del sidebar
  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    if (tab === "settings") {
      setShowSettings(true);
    } else {
      setShowSettings(false);
      setShowStats(false);
    }
    
    // Si va a cámara desde sidebar, solo mostrar la vista sin activar modo automático
    if (tab === "camera") {
      // Reset estados de clasificación automática
      setAutoClassification(null);
      setIsAwaitingConfirmation(false);
    }
  };

  const renderMainContent = () => {
    if (activeTab === "settings") {
      return (
        <div className="flex-1 p-6">
          <div className="text-center text-gray-600">
            <p>Panel de configuración abierto</p>
          </div>
        </div>
      );
    }

    if (activeTab === "stats" || showStats) {
      return <StatsPanel goodCount={goodCount} badCount={badCount} stats={stats} />;
    }

    if (activeTab === "home") {
      return <HomePanel onSelectFruit={handleSelectFruit} selectedFruit={selectedFruit} />;
    }

    if (activeTab === "upload") {
      return (
        <div className="flex-1 p-6">
          <div className="max-w-2xl mx-auto space-y-6">
            {/* Estado de conexión */}
            {backendConnected === false && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-center">
                  <strong>Backend no disponible:</strong> {error}
                </p>
                <button 
                  onClick={checkBackendConnection}
                  className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Reintentar conexión
                </button>
              </div>
            )}

            {backendConnected === true && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-700 text-center">
                  <strong>✓ Backend conectado:</strong> Modelo cargado y listo para procesar imágenes
                </p>
              </div>
            )}

            {/* Componente de subida de imágenes */}
            <ImageUpload 
              onDetectionResult={handleDetectionResult}
              onError={handleApiError}
              disabled={backendConnected === false}
            />

            {/* Mostrar resultados si hay alguno */}
            {detectionResult && (
              <DetectionResults 
                result={detectionResult}
                onClose={() => setDetectionResult(null)}
              />
            )}

            {/* Mostrar error si hay alguno */}
            {error && !detectionResult && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-center">{error}</p>
              </div>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="flex-1 p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
          <ClassificationPanel 
            goodCount={goodCount}
            badCount={badCount}
            onClassify={handleClassify}
            autoClassification={autoClassification}
            confidence={confidence}
            isAwaitingConfirmation={isAwaitingConfirmation}
            onCorrectClassification={handleCorrectClassification}
            onConfirmClassification={handleConfirmClassification}
          />
          <CameraPanel 
            isProcessing={isProcessing}
            lastClassification={lastClassification}
          />
        </div>
        
        {/* Mensaje informativo cuando se está en vista manual */}
        {activeTab === "camera" && !isLive && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-blue-700 text-center">
              <strong>Modo Manual:</strong> Use los botones de clasificación manual o active el botón "MONITOREO" para iniciar la detección automática.
            </p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Header />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeTab={activeTab} onTabChange={handleTabChange} />
        {renderMainContent()}
      </div>
      
      <BottomActions 
        isLive={isLive}
        onToggleLive={handleToggleLive}
        onStartMonitoring={handleStartMonitoring}
        onExit={handleExit}
        onCapture={handleCapture}
        onShowStats={handleShowStats}
      />
      
      <SettingsPanel 
        isOpen={showSettings}
        onClose={() => {
          setShowSettings(false);
          setActiveTab("home");
        }}
      />
    </div>
  );
}