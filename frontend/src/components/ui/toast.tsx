"use client";

import { useEffect } from "react";
import { useToastStore } from "@/store";
import { X } from "lucide-react";

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
}

function Toast({ toast, onClose }: { toast: { id: string; message: string; type: string }; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);

  const colors = {
    success: "border-green-200 bg-green-50 text-green-900",
    error: "border-red-200 bg-red-50 text-red-900",
    info: "border-slate-200 bg-white text-slate-900",
  };

  return (
    <div className={`flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg ${colors[toast.type as keyof typeof colors] || colors.info}`}>
      <span className="text-sm">{toast.message}</span>
      <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function toast(message: string, type: "success" | "error" | "info" = "info") {
  useToastStore.getState().addToast(message, type);
}
