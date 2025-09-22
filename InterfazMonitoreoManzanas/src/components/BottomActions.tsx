import { Monitor, Radio, LogOut, Camera, BarChart3 } from "lucide-react";

interface BottomActionsProps {
  isLive: boolean;
  onToggleLive: () => void;
  onStartMonitoring: () => void;
  onExit: () => void;
  onCapture: () => void;
  onShowStats: () => void;
}

export function BottomActions({ 
  isLive, 
  onToggleLive, 
  onStartMonitoring, 
  onExit, 
  onCapture, 
  onShowStats 
}: BottomActionsProps) {
  return (
    <div className="bg-white border-t border-gray-200 px-6 py-4">
      <div className="flex justify-center gap-4">
        <button
          onClick={onStartMonitoring}
          className="bg-emerald-500 hover:bg-emerald-600 text-white px-8 py-3 rounded-lg transition-colors flex items-center gap-2 uppercase tracking-wide"
        >
          <Monitor className="w-5 h-5" />
          MONITOREO
        </button>
        
        <button
          onClick={onCapture}
          className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-lg transition-colors flex items-center gap-2 uppercase tracking-wide"
        >
          <Camera className="w-5 h-5" />
          CAPTURAR
        </button>
        
        <button
          onClick={onShowStats}
          className="bg-green-700 hover:bg-green-800 text-white px-8 py-3 rounded-lg transition-colors flex items-center gap-2 uppercase tracking-wide"
        >
          <BarChart3 className="w-5 h-5" />
          ESTADÍSTICAS
        </button>
        
        <button
          onClick={onToggleLive}
          className={`px-8 py-3 rounded-lg transition-colors flex items-center gap-2 uppercase tracking-wide ${
            isLive 
              ? "bg-red-500 hover:bg-red-600 text-white" 
              : "bg-gray-300 hover:bg-gray-400 text-gray-700"
          }`}
        >
          <Radio className={`w-5 h-5 ${isLive ? "animate-pulse" : ""}`} />
          LIVE
        </button>
        
        <button
          onClick={onExit}
          className="bg-gray-600 hover:bg-gray-700 text-white px-8 py-3 rounded-lg transition-colors flex items-center gap-2 uppercase tracking-wide"
        >
          <LogOut className="w-5 h-5" />
          SALIR
        </button>
      </div>
    </div>
  );
}