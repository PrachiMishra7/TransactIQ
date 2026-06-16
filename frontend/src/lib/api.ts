import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/api/uploads", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const getUploadStatus = async (uploadId: string) => {
  const { data } = await api.get(`/api/uploads/${uploadId}/status`);
  return data;
};

export const getUploadPreview = async (uploadId: string) => {
  const { data } = await api.get(`/api/uploads/${uploadId}/preview`);
  return data;
};

export const getUploadResults = async (uploadId: string) => {
  const { data } = await api.get(`/api/uploads/${uploadId}/results`);
  return data;
};

export const getUploadErrors = async (uploadId: string, params: Record<string, string | number>) => {
  const { data } = await api.get(`/api/uploads/${uploadId}/errors`, { params });
  return data;
};

export const listUploads = async (page = 1) => {
  const { data } = await api.get("/api/uploads", { params: { page } });
  return data;
};

export const getDashboardStats = async () => {
  const { data } = await api.get("/api/dashboard/stats");
  return data;
};

export const getErrorsByType = async () => {
  const { data } = await api.get("/api/dashboard/charts/errors-by-type");
  return data;
};

export const getFilesPerDay = async () => {
  const { data } = await api.get("/api/dashboard/charts/files-per-day");
  return data;
};

export const getQualityTrend = async () => {
  const { data } = await api.get("/api/dashboard/charts/quality-trend");
  return data;
};

export const getCountryErrors = async () => {
  const { data } = await api.get("/api/dashboard/charts/country-errors");
  return data;
};

export const listRules = async () => {
  const { data } = await api.get("/api/rules");
  return data;
};

export const createRule = async (rule: Record<string, unknown>) => {
  const { data } = await api.post("/api/rules", rule);
  return data;
};

export const updateRule = async (id: string, rule: Record<string, unknown>) => {
  const { data } = await api.put(`/api/rules/${id}`, rule);
  return data;
};

export const deleteRule = async (id: string) => {
  const { data } = await api.delete(`/api/rules/${id}`);
  return data;
};

export const seedRules = async () => {
  const { data } = await api.post("/api/rules/seed");
  return data;
};

export const chunkFile = async (file: File, chunkBy: string, chunkSize: number) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post(`/api/uploads/chunk?chunk_by=${chunkBy}&chunk_size=${chunkSize}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const getDownloadUrl = (uploadId: string, fileType: string) =>
  `${API_URL}/api/uploads/${uploadId}/download/${fileType}`;
