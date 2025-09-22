import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { TrendingUp, TrendingDown, Target, Clock, RefreshCw, Trash2 } from "lucide-react";
import { StatsResponse } from "../services/api";
import { Button } from "./ui/button";

interface StatsPanelProps {
  goodCount: number;
  badCount: number;
  stats?: StatsResponse | null;
  onResetStats?: () => void;
}

export function StatsPanel({ goodCount, badCount, stats, onResetStats }: StatsPanelProps) {
  const total = goodCount + badCount;
  const successRate = total > 0 ? Math.round((goodCount / total) * 100) : 0;
  
  // Usar datos del backend si están disponibles
  const backendStats = stats?.summary;
  const totalDetections = backendStats?.total_detections || total;
  const totalFruits = backendStats?.total_fruits || total;
  const totalNonFruits = backendStats?.total_non_fruits || 0;
  const backendSuccessRate = backendStats?.success_rate ? Math.round(backendStats.success_rate * 100) : successRate;

  const barData = [
    {
      name: "Buenas",
      count: goodCount,
      fill: "#10b981"
    },
    {
      name: "Malas",
      count: badCount,
      fill: "#ef4444"
    }
  ];

  const pieData = [
    {
      name: "Buenas",
      value: goodCount,
      color: "#10b981"
    },
    {
      name: "Malas",
      value: badCount,
      color: "#ef4444"
    }
  ];

  const hourlyData = [
    { hour: "08:00", good: 45, bad: 5 },
    { hour: "09:00", good: 52, bad: 8 },
    { hour: "10:00", good: 38, bad: 12 },
    { hour: "11:00", good: 43, bad: 7 },
    { hour: "12:00", good: 35, bad: 15 },
    { hour: "13:00", good: 41, bad: 9 },
    { hour: "14:00", good: 48, bad: 6 },
    { hour: "15:00", good: 39, bad: 11 }
  ];

  return (
    <div className="flex-1 p-6 bg-gray-50">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl text-gray-800">Estadísticas de Clasificación</h2>
            {onResetStats && (
              <Button
                variant="outline"
                size="sm"
                onClick={onResetStats}
                className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4" />
                Resetear Estadísticas
              </Button>
            )}
          </div>
          
          {/* Métricas principales */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-emerald-600 text-sm">Frutas Buenas</p>
                  <p className="text-2xl text-emerald-800">{goodCount}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-emerald-600" />
              </div>
            </div>

            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-red-600 text-sm">Frutas Malas</p>
                  <p className="text-2xl text-red-800">{badCount}</p>
                </div>
                <TrendingDown className="w-8 h-8 text-red-600" />
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-600 text-sm">Total Procesadas</p>
                  <p className="text-2xl text-blue-800">{totalDetections}</p>
                </div>
                <Target className="w-8 h-8 text-blue-600" />
              </div>
            </div>

            <div className="bg-teal-50 p-4 rounded-lg border border-teal-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-teal-600 text-sm">Tasa de Éxito</p>
                  <p className="text-2xl text-teal-800">{backendSuccessRate}%</p>
                </div>
                <Clock className="w-8 h-8 text-teal-600" />
              </div>
            </div>
          </div>

          {/* Gráficos */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gráfico de barras */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg text-gray-700 mb-4">Clasificación Total</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Gráfico circular */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg text-gray-700 mb-4">Distribución Porcentual</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>

        {/* Histórico por horas */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg text-gray-700 mb-4">Rendimiento por Hora (Hoy)</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="good" stackId="a" fill="#10b981" name="Buenas" radius={[0, 0, 0, 0]} />
                <Bar dataKey="bad" stackId="a" fill="#ef4444" name="Malas" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Información adicional */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h4 className="text-gray-700 mb-2">Frutas Detectadas</h4>
            <p className="text-2xl text-gray-800">{totalFruits}</p>
            <p className="text-sm text-gray-600">de {totalDetections} total</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h4 className="text-gray-700 mb-2">No Frutas</h4>
            <p className="text-2xl text-gray-800">{totalNonFruits}</p>
            <p className="text-sm text-gray-600">imágenes sin fruta</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h4 className="text-gray-700 mb-2">Última Actualización</h4>
            <p className="text-sm text-gray-800">
              {stats?.last_updated ? 
                new Date(stats.last_updated).toLocaleString() : 
                'No disponible'
              }
            </p>
            <p className="text-sm text-gray-600">desde el backend</p>
          </div>
        </div>

        {/* Información del backend si está disponible */}
        {stats && (
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg text-gray-700 mb-4">Información del Backend</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-medium text-gray-600 mb-2">Tipos de Fruta Detectados</h4>
                <div className="space-y-1">
                  {Object.entries(backendStats?.fruits_by_type || {}).map(([type, count]) => (
                    <div key={type} className="flex justify-between">
                      <span>{type}:</span>
                      <span className="font-mono">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-600 mb-2">Estados de Fruta</h4>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span>OK:</span>
                    <span className="font-mono text-green-600">{backendStats?.fruits_by_status?.OK || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>MALOGRADA:</span>
                    <span className="font-mono text-red-600">{backendStats?.fruits_by_status?.MALOGRADA || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}