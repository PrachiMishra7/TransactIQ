"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { History, ExternalLink, Download } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { listUploads, getDownloadUrl } from "@/lib/api";
import { formatBytes, formatNumber, getQualityLabel } from "@/lib/utils";

export default function HistoryPage() {
  const { data, isLoading } = useQuery({ queryKey: ["uploads"], queryFn: () => listUploads() });

  return (
    <DashboardLayout title="Upload History" description="View previous uploads and re-download reports">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" /> Historical Uploads
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-center text-slate-400 py-8">Loading...</p>
          ) : !data?.uploads?.length ? (
            <p className="text-center text-slate-400 py-8">No uploads yet. <Link href="/upload" className="text-indigo-600 hover:underline">Upload a file</Link> to get started.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-slate-50">
                    <th className="px-4 py-3 text-left font-medium text-slate-600">File Name</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Size</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Records</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Quality</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Date</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.uploads.map((u: {
                    id: string; file_name: string; file_size: number; total_rows: number;
                    quality_score: number; status: string; created_at: string;
                  }) => (
                    <tr key={u.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-900">{u.file_name}</td>
                      <td className="px-4 py-3 text-slate-600">{formatBytes(u.file_size)}</td>
                      <td className="px-4 py-3 text-slate-600">{formatNumber(u.total_rows)}</td>
                      <td className="px-4 py-3">
                        {u.status === "COMPLETED" ? (
                          <span className="font-semibold text-indigo-600">{u.quality_score}/100</span>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={u.status === "COMPLETED" ? "success" : u.status === "FAILED" ? "destructive" : "secondary"}>
                          {u.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{new Date(u.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {u.status === "COMPLETED" && (
                            <>
                              <Link href={`/results/${u.id}`}>
                                <Button variant="ghost" size="sm"><ExternalLink className="h-4 w-4" /></Button>
                              </Link>
                              <Button variant="ghost" size="sm" onClick={() => window.open(getDownloadUrl(u.id, "report"), "_blank")}>
                                <Download className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                          {u.status !== "COMPLETED" && u.status !== "FAILED" && (
                            <Link href={`/processing/${u.id}`}>
                              <Button variant="outline" size="sm">View Progress</Button>
                            </Link>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
