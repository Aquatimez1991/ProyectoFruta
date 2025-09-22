import { ImageWithFallback } from "./figma/ImageWithFallback";

interface CameraPanelProps {
  isProcessing: boolean;
  lastClassification: string | null;
}

export function CameraPanel({ isProcessing, lastClassification }: CameraPanelProps) {
  const getStatusText = () => {
    if (isProcessing) return "Reconociendo...";
    if (lastClassification) return `Clasificada: ${lastClassification}`;
    return "En espera";
  };

  const getStatusColor = () => {
    if (isProcessing) return "text-yellow-600";
    if (lastClassification === "BUENA") return "text-emerald-600";
    if (lastClassification === "MALA") return "text-red-600";
    return "text-gray-600";
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg mb-6 text-gray-800">Vista de Cámara en Tiempo Real</h3>
      
      <div className="relative">
        <div className="bg-gray-900 rounded-lg p-4 border-4 border-slate-700">
          <div className="aspect-video bg-gray-800 rounded-lg overflow-hidden flex items-center justify-center">
            <ImageWithFallback
              src="https://images.unsplash.com/photo-1623815242959-fb20354f9b8d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMHJlZCUyMGFwcGxlJTIwZnJ1aXR8ZW58MXx8fHwxNzU4NTYxMTIyfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
              alt="Manzana detectada"
              className="w-full h-full object-cover"
            />
          </div>
        </div>
        
        {isProcessing && (
          <div className="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center">
            <div className="bg-white px-4 py-2 rounded-lg flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-gray-800">Procesando...</span>
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
      
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="text-blue-600">Resolución</div>
          <div className="text-blue-800">1920x1080</div>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <div className="text-purple-600">FPS</div>
          <div className="text-purple-800">30</div>
        </div>
      </div>
    </div>
  );
}