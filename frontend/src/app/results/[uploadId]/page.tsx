"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Download, AlertTriangle, CheckCircle, FileText, Sparkles } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { QualityGauge } from "@/components/dashboard/quality-gauge";
import { ErrorTable } from "@/components/errors/error-table";
import { getUploadResults, getDownloadUrl } from "@/lib/api";
import { formatNumber } from "@/lib/utils";
import { Database, CheckCheck, XCircle, AlertCircle } from "lucide-react";

export default function ResultsPage() {
  const params = useParams();
  const uploadId = params.uploadId as string;

  const { data: results, isLoading } = useQuery({
    queryKey: ["results", uploadId],
    queryFn: () => getUploadResults(uploadId),
    enabled: !!uploadId,
  });

  const handleDownload = (type: string) => {
    window.open(getDownloadUrl(uploadId, type), "_blank");
  };

  if (isLoading) {
    return (
      <DashboardLayout title="Results" description="Loading validation results...">
        <div className="flex h-64 items-center justify-center text-slate-400">Loading...</div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Validation Results" description={results?.file_name}>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-5">
        <KpiCard title="Total Records" value={formatNumber(results?.total_records ?? 0)} icon={Database} />
        <KpiCard title="Valid Records" value={formatNumber(results?.valid_records ?? 0)} icon={CheckCheck} />
        <KpiCard title="Invalid Records" value={formatNumber(results?.invalid_records ?? 0)} icon={XCircle} />
        <KpiCard title="Warnings" value={formatNumber(results?.warnings ?? 0)} icon={AlertCircle} />
        <Card className="flex items-center justify-center p-4">
          <QualityGauge score={results?.quality_score ?? 0} size={140} />
        </Card>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><CardTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-indigo-600" /> AI Validation Summary</CardTitle></CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700 font-sans">
              {results?.summary || "No summary available."}
            </pre>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Validation Insights</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: "Top Error", value: results?.insights?.topError },
              { label: "Most Problematic Field", value: results?.insights?.mostProblematicField },
              { label: "Country With Highest Error Rate", value: results?.insights?.countryWithHighestErrorRate },
              { label: "Error Rate", value: results?.insights?.errorRate ? `${results.insights.errorRate}%` : "N/A" },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs font-medium text-slate-500">{label}</p>
                <p className="mt-1 text-sm font-semibold text-slate-900 truncate">{value ?? "N/A"}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Download Reports</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button onClick={() => handleDownload("cleaned")}>
            <Download className="h-4 w-4" /> Download Cleaned File
          </Button>
          <Button variant="outline" onClick={() => handleDownload("errors")}>
            <Download className="h-4 w-4" /> Download Error File
          </Button>
          <Button variant="outline" onClick={() => handleDownload("report")}>
            <FileText className="h-4 w-4" /> Download Summary Report (PDF)
          </Button>
        </CardContent>
      </Card>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" /> Error Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorTable uploadId={uploadId} />
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
