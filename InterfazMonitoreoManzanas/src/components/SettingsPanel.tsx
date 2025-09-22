import { useState } from "react";
import { X } from "lucide-react";
import { Button } from "./ui/button";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Slider } from "./ui/slider";
import { Switch } from "./ui/switch";

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [resolution, setResolution] = useState("1920x1080");
  const [captureFrequency, setCaptureFrequency] = useState([30]);
  const [colorThreshold, setColorThreshold] = useState([75]);
  const [shapeThreshold, setShapeThreshold] = useState([80]);
  const [textureThreshold, setTextureThreshold] = useState([70]);
  const [autoMode, setAutoMode] = useState(true);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl text-gray-800">Configuración del Sistema</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="space-y-6">
          {/* Configuración de Cámara */}
          <div className="space-y-4">
            <h3 className="text-lg text-gray-700 border-b border-gray-200 pb-2">Configuración de Cámara</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="resolution">Resolución</Label>
                <Select value={resolution} onValueChange={setResolution}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar resolución" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1280x720">1280x720 (HD)</SelectItem>
                    <SelectItem value="1920x1080">1920x1080 (Full HD)</SelectItem>
                    <SelectItem value="2560x1440">2560x1440 (2K)</SelectItem>
                    <SelectItem value="3840x2160">3840x2160 (4K)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="frequency">Frecuencia de Captura (FPS)</Label>
                <div className="px-2">
                  <Slider
                    value={captureFrequency}
                    onValueChange={setCaptureFrequency}
                    max={60}
                    min={1}
                    step={1}
                    className="w-full"
                  />
                  <div className="text-center text-sm text-gray-600 mt-1">
                    {captureFrequency[0]} FPS
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Umbrales de Clasificación */}
          <div className="space-y-4">
            <h3 className="text-lg text-gray-700 border-b border-gray-200 pb-2">Umbrales de Clasificación</h3>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="color-threshold">Umbral de Color (%)</Label>
                <div className="px-2">
                  <Slider
                    value={colorThreshold}
                    onValueChange={setColorThreshold}
                    max={100}
                    min={0}
                    step={5}
                    className="w-full"
                  />
                  <div className="text-center text-sm text-gray-600 mt-1">
                    {colorThreshold[0]}%
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="shape-threshold">Umbral de Forma (%)</Label>
                <div className="px-2">
                  <Slider
                    value={shapeThreshold}
                    onValueChange={setShapeThreshold}
                    max={100}
                    min={0}
                    step={5}
                    className="w-full"
                  />
                  <div className="text-center text-sm text-gray-600 mt-1">
                    {shapeThreshold[0]}%
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="texture-threshold">Umbral de Textura (%)</Label>
                <div className="px-2">
                  <Slider
                    value={textureThreshold}
                    onValueChange={setTextureThreshold}
                    max={100}
                    min={0}
                    step={5}
                    className="w-full"
                  />
                  <div className="text-center text-sm text-gray-600 mt-1">
                    {textureThreshold[0]}%
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Modo de Operación */}
          <div className="space-y-4">
            <h3 className="text-lg text-gray-700 border-b border-gray-200 pb-2">Modo de Operación</h3>
            
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="space-y-1">
                <Label htmlFor="auto-mode">Modo Automático</Label>
                <p className="text-sm text-gray-600">
                  Clasificación automática cuando se detecta una manzana
                </p>
              </div>
              <Switch
                id="auto-mode"
                checked={autoMode}
                onCheckedChange={setAutoMode}
              />
            </div>
          </div>

          {/* Botones de Acción */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <Button variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button onClick={onClose} className="bg-teal-600 hover:bg-teal-700">
              Guardar Configuración
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}