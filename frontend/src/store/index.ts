import { create } from "zustand";

interface UploadState {
  uploadId: string | null;
  fileName: string | null;
  status: string;
  progress: number;
  setUpload: (id: string, fileName: string) => void;
  setStatus: (status: string, progress: number) => void;
  reset: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  uploadId: null,
  fileName: null,
  status: "idle",
  progress: 0,
  setUpload: (id, fileName) => set({ uploadId: id, fileName, status: "UPLOADING", progress: 5 }),
  setStatus: (status, progress) => set({ status, progress }),
  reset: () => set({ uploadId: null, fileName: null, status: "idle", progress: 0 }),
}));

interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

interface ToastState {
  toasts: Toast[];
  addToast: (message: string, type?: Toast["type"]) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (message, type = "info") =>
    set((s) => ({
      toasts: [...s.toasts, { id: crypto.randomUUID(), message, type }],
    })),
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
