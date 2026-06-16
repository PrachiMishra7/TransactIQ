"use client";

import { useQuery } from "@tanstack/react-query";
import { FileCheck, Database, TrendingUp, Shield } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorsByTypeChart, FilesPerDayChart, QualityTrendChart, CountryErrorsChart } from "@/components/dashboard/charts";
import { getDashboardStats, getErrorsByType, getFilesPerDay, getQualityTrend, getCountryErrors, seedRules } from "@/lib/api";
import { formatNumber } from "@/lib/utils";
import { useEffect } from "react";

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({ queryKey: ["dashboard-stats"], queryFn: getDashboardStats });
  const { data: errorsByType } = useQuery({ queryKey: ["errors-by-type"], queryFn: getErrorsByType });
  const { data: filesPerDay } = useQuery({ queryKey: ["files-per-day"], queryFn: getFilesPerDay });
  const { data: qualityTrend } = useQuery({ queryKey: ["quality-trend"], queryFn: getQualityTrend });
  const { data: countryErrors } = useQuery({ queryKey: ["country-errors"], queryFn: getCountryErrors });

  useEffect(() => {
    seedRules().catch(() => {});
  }, []);

  return (
    <DashboardLayout title="Dashboard" description="Transaction data quality overview and analytics">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard title="Total Files Processed" value={isLoading ? "..." : formatNumber(stats?.total_files_processed ?? 0)} icon={FileCheck} />
        <KpiCard title="Total Records Validated" value={isLoading ? "..." : formatNumber(stats?.total_records_validated ?? 0)} icon={Database} />
        <KpiCard title="Average Quality Score" value={isLoading ? "..." : `${stats?.average_quality_score ?? 0}/100`} icon={TrendingUp} />
        <KpiCard title="Active Validation Rules" value={isLoading ? "..." : stats?.active_validation_rules ?? 0} icon={Shield} />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Validation Errors by Type</CardTitle></CardHeader>
          <CardContent><ErrorsByTypeChart data={errorsByType ?? []} /></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Files Processed Per Day</CardTitle></CardHeader>
          <CardContent><FilesPerDayChart data={filesPerDay ?? []} /></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Quality Score Trend</CardTitle></CardHeader>
          <CardContent><QualityTrendChart data={qualityTrend ?? []} /></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Country-wise Error Distribution</CardTitle></CardHeader>
          <CardContent><CountryErrorsChart data={countryErrors ?? []} /></CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
