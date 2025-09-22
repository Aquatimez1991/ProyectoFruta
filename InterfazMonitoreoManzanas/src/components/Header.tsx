import { Camera, Apple } from "lucide-react";

export function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 bg-teal-100 rounded-lg">
          <Apple className="w-6 h-6 text-teal-600" />
        </div>
        <h1 className="text-2xl text-gray-800">Detección de Manzanas</h1>
      </div>
    </header>
  );
}