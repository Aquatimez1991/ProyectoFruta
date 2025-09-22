import { CheckCircle, XCircle, RotateCcw, Check } from "lucide-react";

interface ClassificationPanelProps {
  goodCount: number;
  badCount: number;
  onClassify: (type: 'good' | 'bad') => void;
  autoClassification: string | null;
  confidence: number;
  isAwaitingConfirmation: boolean;
  onCorrectClassification: () => void;
  onConfirmClassification: () => void;
}

export function ClassificationPanel({ 
  goodCount, 
  badCount, 
  onClassify, 
  autoClassification,
  confidence,
  isAwaitingConfirmation,
  onCorrectClassification,
  onConfirmClassification
}: ClassificationPanelProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg mb-6 text-gray-800">Clasificación de Fruta</h3>
      
      {/* Clasificación Automática */}
      {autoClassification && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-blue-700">Clasificación automática:</span>
              <span className={`px-3 py-1 rounded-full text-white ${
                autoClassification === 'BUENA' ? 'bg-emerald-500' : 'bg-red-500'
              }`}>
                {autoClassification}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-blue-700">Confianza:</span>
              <span className="text-blue-800">{confidence}%</span>
            </div>

            {isAwaitingConfirmation && (
              <div className="mt-4 space-y-2">
                <p className="text-sm text-yellow-700 bg-yellow-50 p-2 rounded border border-yellow-200">
                  Esperando confirmación del operador...
                </p>
                
                <div className="flex gap-2">
                  <button
                    onClick={onCorrectClassification}
                    className={`flex-1 py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 ${
                      autoClassification === 'BUENA' 
                        ? 'bg-red-500 hover:bg-red-600 text-white' 
                        : 'bg-emerald-500 hover:bg-emerald-600 text-white'
                    }`}
                  >
                    <RotateCcw className="w-4 h-4" />
                    {autoClassification === 'BUENA' ? 'Corregir a MALA' : 'Corregir a BUENA'}
                  </button>
                  
                  <button
                    onClick={onConfirmClassification}
                    className="flex-1 bg-gray-400 hover:bg-gray-500 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    <Check className="w-4 h-4" />
                    Confirmar clasificación
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Botones de Clasificación Manual */}
      <div className="space-y-4">
        <button
          onClick={() => onClassify('good')}
          disabled={isAwaitingConfirmation}
          className={`w-full py-4 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 ${
            isAwaitingConfirmation 
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
              : 'bg-emerald-500 hover:bg-emerald-600 text-white'
          }`}
        >
          <CheckCircle className="w-6 h-6" />
          <span className="uppercase tracking-wide">BUENA</span>
        </button>
        
        <button
          onClick={() => onClassify('bad')}
          disabled={isAwaitingConfirmation}
          className={`w-full py-4 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 ${
            isAwaitingConfirmation 
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
              : 'bg-red-500 hover:bg-red-600 text-white'
          }`}
        >
          <XCircle className="w-6 h-6" />
          <span className="uppercase tracking-wide">MALA</span>
        </button>
      </div>
      
      <div className="mt-8 space-y-3">
        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
          <span className="text-gray-600">Frutas Buenas:</span>
          <span className="bg-emerald-500 text-white px-3 py-1 rounded-full">{goodCount}</span>
        </div>
        
        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
          <span className="text-gray-600">Frutas Malas:</span>
          <span className="bg-red-500 text-white px-3 py-1 rounded-full">{badCount}</span>
        </div>
        
        <div className="flex justify-between items-center p-3 bg-teal-50 rounded-lg border border-teal-200">
          <span className="text-teal-700">Total Procesadas:</span>
          <span className="bg-teal-600 text-white px-3 py-1 rounded-full">{goodCount + badCount}</span>
        </div>
      </div>
    </div>
  );
}