"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Scissors, Upload, Download } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/input";
import { chunkFile } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import { formatBytes, formatNumber } from "@/lib/utils";

export default function ChunkingPage() {
  const [file, setFile] = useState<File | null>(null);
  const [chunkBy, setChunkBy] = useState("row_count");
  const [chunkSize, setChunkSize] = useState(1000);
  const [result, setResult] = useState<{ total_chunks: number; chunks: { chunk_number: number; filename: string; row_count: number; file_size: number }[] } | null>(null);
  const [loading, setLoading] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) { setFile(accepted[0]); setResult(null); }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    maxFiles: 1,
  });

  const handleChunk = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const data = await chunkFile(file, chunkBy, chunkSize);
      setResult(data);
      toast(`Split into ${data.total_chunks} chunks`, "success");
    } catch {
      toast("Chunking failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout title="CSV Chunking Engine" description="Split large CSV files by row count or file size">
      <div className="mx-auto max-w-3xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Scissors className="h-5 w-5" /> Split Large Files</CardTitle>
            <CardDescription>Handle files with millions of rows by splitting into manageable chunks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div
              {...getRootProps()}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors ${
                isDragActive ? "border-indigo-500 bg-indigo-50" : "border-slate-200 hover:border-indigo-300"
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="mb-3 h-10 w-10 text-indigo-400" />
              <p className="text-sm text-slate-600">{file ? file.name : "Drop CSV file here or click to browse"}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Split By</Label>
                <Select value={chunkBy} onChange={e => setChunkBy(e.target.value)}>
                  <option value="row_count">Row Count</option>
                  <option value="file_size">File Size (bytes)</option>
                </Select>
              </div>
              <div>
                <Label>{chunkBy === "row_count" ? "Rows Per Chunk" : "Max Chunk Size (bytes)"}</Label>
                <Input type="number" value={chunkSize} onChange={e => setChunkSize(Number(e.target.value))} min={100} />
              </div>
            </div>

            <Button className="w-full" disabled={!file || loading} onClick={handleChunk}>
              {loading ? "Processing..." : "Split File"}
            </Button>
          </CardContent>
        </Card>

        {result && (
          <Card>
            <CardHeader>
              <CardTitle>{result.total_chunks} Chunks Created</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-slate-50">
                    <th className="px-4 py-2 text-left">Chunk</th>
                    <th className="px-4 py-2 text-left">Filename</th>
                    <th className="px-4 py-2 text-left">Rows</th>
                    <th className="px-4 py-2 text-left">Size</th>
                  </tr>
                </thead>
                <tbody>
                  {result.chunks.map(c => (
                    <tr key={c.chunk_number} className="border-b">
                      <td className="px-4 py-2">{c.chunk_number}</td>
                      <td className="px-4 py-2 font-mono text-xs">{c.filename}</td>
                      <td className="px-4 py-2">{formatNumber(c.row_count)}</td>
                      <td className="px-4 py-2">{formatBytes(c.file_size)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
