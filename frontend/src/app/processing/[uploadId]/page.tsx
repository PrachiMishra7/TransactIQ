"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/badge";
import { getUploadStatus, getUploadPreview } from "@/lib/api";
import { useUploadStore } from "@/store";

const STEPS = [
  { key: "UPLOADING", label: "Uploading" },
  { key: "PARSING", label: "Parsing" },
  { key: "VALIDATING", label: "Validating" },
  { key: "CLEANING", label: "Cleaning" },
  { key: "GENERATING_REPORTS", label: "Generating Reports" },
  { key: "COMPLETED", label: "Completed" },
];

export default function ProcessingPage() {
  const params = useParams();
  const uploadId = params.uploadId as string;
  const router = useRouter();
  const { setStatus } = useUploadStore();

  const { data: status } = useQuery({
    queryKey: ["status", uploadId],
    queryFn: () => getUploadStatus(uploadId),
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === "COMPLETED" || s === "FAILED" ? false : 1000;
    },
    enabled: !!uploadId,
  });

  const { data: preview } = useQuery({
    queryKey: ["preview", uploadId],
    queryFn: () => getUploadPreview(uploadId),
    enabled: !!uploadId,
  });

  useEffect(() => {
    if (status) {
      setStatus(status.status, status.progress);
      if (status.status === "COMPLETED") {
        setTimeout(() => router.push(`/results/${uploadId}`), 1500);
      }
    }
  }, [status, uploadId, router, setStatus]);

  const currentIdx = STEPS.findIndex(s => s.key === status?.status);

  return (
    <DashboardLayout title="Processing" description={status?.file_name ?? "Processing your dataset..."}>
      <div className="mx-auto max-w-3xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Processing Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="mb-2 flex justify-between text-sm">
                <span className="text-slate-600">{status?.status?.replace(/_/g, " ") ?? "Starting..."}</span>
                <span className="font-medium text-indigo-600">{status?.progress ?? 0}%</span>
              </div>
              <Progress value={status?.progress ?? 0} />
            </div>

            <div className="space-y-3">
              {STEPS.map((step, idx) => {
                const done = currentIdx > idx || status?.status === "COMPLETED";
                const active = currentIdx === idx && status?.status !== "COMPLETED";
                return (
                  <div key={step.key} className="flex items-center gap-3">
                    {done ? (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    ) : active ? (
                      <Loader2 className="h-5 w-5 animate-spin text-indigo-600" />
                    ) : (
                      <Circle className="h-5 w-5 text-slate-300" />
                    )}
                    <span className={`text-sm ${done ? "text-green-700 font-medium" : active ? "text-indigo-700 font-medium" : "text-slate-400"}`}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {preview && (
          <Card>
            <CardHeader>
              <CardTitle>Dataset Preview (First 20 Rows)</CardTitle>
            </CardHeader>
            <CardContent>
              {preview.column_mapping && (
                <div className="mb-4 flex flex-wrap gap-2">
                  {Object.entries(preview.column_mapping as Record<string, string>).map(([orig, mapped]) => (
                    orig !== mapped && (
                      <span key={orig} className="rounded bg-indigo-50 px-2 py-1 text-xs text-indigo-700">
                        {orig} → {mapped as string}
                      </span>
                    )
                  ))}
                </div>
              )}
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b bg-slate-50">
                      {preview.columns?.map((col: string) => (
                        <th key={col} className="px-3 py-2 text-left font-medium text-slate-600">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.rows?.slice(0, 20).map((row: Record<string, string>, i: number) => (
                      <tr key={i} className="border-b border-slate-100">
                        {preview.columns?.map((col: string) => (
                          <td key={col} className="px-3 py-2 text-slate-700 max-w-[150px] truncate">{row[col]}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
