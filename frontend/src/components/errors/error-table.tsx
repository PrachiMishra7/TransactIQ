"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Download, ChevronLeft, ChevronRight } from "lucide-react";
import { getUploadErrors } from "@/lib/api";
import { Input, Select } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getSeverityColor } from "@/lib/utils";

interface ErrorTableProps {
  uploadId: string;
}

export function ErrorTable({ uploadId }: ErrorTableProps) {
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["errors", uploadId, search, severity, page],
    queryFn: () => getUploadErrors(uploadId, {
      search: search || undefined,
      severity: severity || undefined,
      page,
      page_size: 20,
      sort_by: "row_number",
      sort_order: "asc",
    } as Record<string, string | number>),
    enabled: !!uploadId,
  });

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0;

  const handleExport = () => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/uploads/${uploadId}/download/errors`, "_blank");
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Search errors..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-9"
          />
        </div>
        <Select value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1); }}>
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </Select>
        <Button variant="outline" onClick={handleExport}>
          <Download className="h-4 w-4" /> Export
        </Button>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="px-4 py-3 text-left font-medium text-slate-600">Row</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Column</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Error Type</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Message</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Severity</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">Loading errors...</td></tr>
            ) : data?.errors?.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">No errors found</td></tr>
            ) : (
              data?.errors?.map((err: { id: string; row_number: number; column_name: string; error_type: string; error_message: string; severity: string }) => (
                <tr key={err.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono text-slate-700">{err.row_number}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">{err.column_name}</td>
                  <td className="px-4 py-3 text-slate-600">{err.error_type.replace(/_/g, " ")}</td>
                  <td className="px-4 py-3 text-slate-600 max-w-xs truncate">{err.error_message}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${getSeverityColor(err.severity)}`}>
                      {err.severity}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">{data?.total} total errors</p>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm text-slate-600">Page {page} of {totalPages}</span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
