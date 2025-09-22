import { Home, Settings, Camera, Upload } from "lucide-react";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const menuItems = [
    { id: "home", icon: Home, label: "Inicio" },
    { id: "upload", icon: Upload, label: "Subir Imagen" },
    { id: "camera", icon: Camera, label: "Cámara" },
    { id: "settings", icon: Settings, label: "Configuración" },
  ];

  return (
    <aside className="w-20 bg-slate-700 flex flex-col items-center py-6 space-y-4">
      {menuItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        
        return (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`
              w-12 h-12 rounded-lg flex items-center justify-center transition-colors
              ${isActive 
                ? "bg-teal-600 text-white" 
                : "text-gray-300 hover:bg-slate-600 hover:text-white"
              }
            `}
            title={item.label}
          >
            <Icon className="w-6 h-6" />
          </button>
        );
      })}
    </aside>
  );
}