import { Apple, CheckCircle, Clock } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

interface Fruit {
  id: string;
  name: string;
  image: string;
  status: "available" | "development" | "coming-soon";
  isDefault?: boolean;
}

interface HomePanelProps {
  onSelectFruit: (fruitId: string) => void;
  selectedFruit: string;
}

export function HomePanel({ onSelectFruit, selectedFruit }: HomePanelProps) {
  const fruits: Fruit[] = [
    {
      id: "apple",
      name: "Manzana",
      image: "https://images.unsplash.com/photo-1623815242959-fb20354f9b8d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMHJlZCUyMGFwcGxlJTIwZnJ1aXR8ZW58MXx8fHwxNzU4NTYxMTIyfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      status: "available",
      isDefault: true
    },
    {
      id: "orange",
      name: "Naranja",
      image: "https://images.unsplash.com/photo-1641069765777-bbe635be1f1d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxvcmFuZ2UlMjBjaXRydXMlMjBmcnVpdHxlbnwxfHx8fDE3NTg0Nzg1MDl8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      status: "development"
    },
    {
      id: "banana",
      name: "Plátano",
      image: "https://images.unsplash.com/photo-1661225535262-ed219d29b7b6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiYW5hbmElMjB5ZWxsb3clMjBmcnVpdHxlbnwxfHx8fDE3NTg1NDgwOTh8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      status: "coming-soon"
    },
    {
      id: "strawberry",
      name: "Fresa",
      image: "https://images.unsplash.com/photo-1604949851132-13304b6ecd8a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzdHJhd2JlcnJ5JTIwcmVkJTIwZnJ1aXR8ZW58MXx8fHwxNzU4NTYxOTMxfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      status: "coming-soon"
    }
  ];

  const getStatusInfo = (status: string) => {
    switch (status) {
      case "available":
        return {
          icon: CheckCircle,
          text: "Disponible",
          color: "text-emerald-600",
          bgColor: "bg-emerald-50",
          borderColor: "border-emerald-200"
        };
      case "development":
        return {
          icon: Clock,
          text: "En desarrollo",
          color: "text-yellow-600",
          bgColor: "bg-yellow-50",
          borderColor: "border-yellow-200"
        };
      default:
        return {
          icon: Clock,
          text: "Próximamente",
          color: "text-gray-500",
          bgColor: "bg-gray-50",
          borderColor: "border-gray-200"
        };
    }
  };

  return (
    <div className="flex-1 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-2xl text-gray-800 mb-2">Selección de Fruta para Monitoreo</h2>
          <p className="text-gray-600">Selecciona la fruta que deseas monitorear con el sistema de detección</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {fruits.map((fruit) => {
            const statusInfo = getStatusInfo(fruit.status);
            const StatusIcon = statusInfo.icon;
            const isSelected = selectedFruit === fruit.id;
            const isDisabled = fruit.status !== "available";

            return (
              <div
                key={fruit.id}
                className={`
                  relative bg-white rounded-xl border-2 p-6 transition-all cursor-pointer hover:shadow-lg
                  ${isSelected 
                    ? "border-teal-500 ring-4 ring-teal-100" 
                    : `${statusInfo.borderColor} hover:border-teal-300`
                  }
                  ${isDisabled ? "opacity-60" : ""}
                `}
                onClick={() => !isDisabled && onSelectFruit(fruit.id)}
              >
                {fruit.isDefault && (
                  <div className="absolute -top-2 -right-2 bg-teal-600 text-white px-2 py-1 rounded-lg text-xs">
                    Predeterminada
                  </div>
                )}

                <div className="text-center space-y-4">
                  <div className="w-24 h-24 mx-auto rounded-full overflow-hidden bg-gray-100">
                    <ImageWithFallback
                      src={fruit.image}
                      alt={fruit.name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <div>
                    <h3 className="text-lg text-gray-800 mb-2">{fruit.name}</h3>
                    
                    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${statusInfo.bgColor} ${statusInfo.borderColor} border`}>
                      <StatusIcon className={`w-4 h-4 ${statusInfo.color}`} />
                      <span className={`text-sm ${statusInfo.color}`}>
                        {statusInfo.text}
                      </span>
                    </div>
                  </div>

                  {fruit.status === "available" && (
                    <button
                      className={`w-full py-2 px-4 rounded-lg transition-colors ${
                        isSelected
                          ? "bg-teal-600 text-white"
                          : "bg-teal-100 text-teal-700 hover:bg-teal-200"
                      }`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectFruit(fruit.id);
                      }}
                    >
                      {isSelected ? "Seleccionada" : "Seleccionar"}
                    </button>
                  )}

                  {fruit.status !== "available" && (
                    <button
                      disabled
                      className="w-full py-2 px-4 rounded-lg bg-gray-200 text-gray-500 cursor-not-allowed"
                    >
                      No disponible
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-8 p-6 bg-teal-50 rounded-lg border border-teal-200">
          <div className="flex items-center gap-3">
            <Apple className="w-6 h-6 text-teal-600" />
            <div>
              <h4 className="text-teal-800">Sistema Activo</h4>
              <p className="text-teal-600 text-sm">
                Actualmente configurado para detectar: <span className="font-medium">Manzana</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}