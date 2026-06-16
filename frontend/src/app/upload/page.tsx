"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { Upload, FileSpreadsheet, X } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { uploadFile } from "@/lib/api";
import { useUploadStore } from "@/store";
import { toast } from "@/components/ui/toast";
import { formatBytes } from "@/lib/utils";

export default function UploadPage() {
  const router = useRouter();
  const { setUpload } = useUploadStore();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    maxFiles: 1,
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadFile(file);
      setUpload(result.upload_id, result.file_name);
      toast("File uploaded successfully. Processing started.", "success");
      router.push(`/processing/${result.upload_id}`);
    } catch {
      toast("Upload failed. Please try again.", "error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <DashboardLayout title="Upload Dataset" description="Upload transaction CSV or XLSX files for validation and cleaning">
      <div className="mx-auto max-w-3xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Drag & Drop Upload</CardTitle>
            <CardDescription>Supports CSV and XLSX files with order, product, and payment data</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              {...getRootProps()}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors ${
                isDragActive ? "border-indigo-500 bg-indigo-50" : "border-slate-200 hover:border-indigo-300 hover:bg-slate-50"
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="mb-4 h-12 w-12 text-indigo-400" />
              <p className="text-lg font-medium text-slate-700">
                {isDragActive ? "Drop your file here" : "Drag & drop your file here"}
              </p>
              <p className="mt-1 text-sm text-slate-400">or click to browse</p>
              <p className="mt-4 text-xs text-slate-400">CSV, XLSX up to 50MB</p>
            </div>

            {file && (
              <div className="mt-4 flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center gap-3">
                  <FileSpreadsheet className="h-8 w-8 text-indigo-600" />
                  <div>
                    <p className="font-medium text-slate-900">{file.name}</p>
                    <p className="text-sm text-slate-500">{formatBytes(file.size)}</p>
                  </div>
                </div>
                <button onClick={() => setFile(null)} className="text-slate-400 hover:text-slate-600">
                  <X className="h-5 w-5" />
                </button>
              </div>
            )}

            <Button className="mt-6 w-full" disabled={!file || uploading} onClick={handleUpload}>
              {uploading ? "Uploading..." : "Upload & Process"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Expected Columns</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
              {["order_id", "customer_name", "phone", "email", "address", "order_date", "delivery_date",
                "sku", "quantity", "unit_price", "total_price", "payment_method", "transaction_id", "country"].map(col => (
                <div key={col} className="rounded-lg bg-slate-50 px-3 py-2 font-mono text-xs text-slate-600">{col}</div>
              ))}
            </div>
            <p className="mt-4 text-xs text-slate-400">
              Smart column mapping automatically detects variants like mobile, phone_no, contact_number → phone
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
