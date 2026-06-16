"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, CartesianGrid, Legend } from "recharts";

const COLORS = ["#6366f1", "#8b5cf6", "#ec4899", "#f97316", "#eab308", "#22c55e", "#06b6d4", "#64748b"];

export function ErrorsByTypeChart({ data }: { data: { type: string; count: number }[] }) {
  if (!data.length) {
    return <EmptyChart message="No validation errors yet" />;
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={data} dataKey="count" nameKey="type" cx="50%" cy="50%" outerRadius={100} label={({ type, percent }) => `${type} (${((percent ?? 0) * 100).toFixed(0)}%)`}>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function FilesPerDayChart({ data }: { data: { date: string; count: number }[] }) {
  if (!data.length) {
    return <EmptyChart message="No uploads in the last 30 days" />;
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} name="Files" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function QualityTrendChart({ data }: { data: { date: string; score: number; file_name: string }[] }) {
  if (!data.length) {
    return <EmptyChart message="No quality score data yet" />;
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
        <Tooltip formatter={(v) => [`${v}/100`, "Quality Score"]} />
        <Legend />
        <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} dot={{ fill: "#6366f1" }} name="Quality Score" />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function CountryErrorsChart({ data }: { data: { country: string; count: number }[] }) {
  if (!data.length || data.every((d) => d.count === 0)) {
    return <EmptyChart message="No country-specific errors yet" />;
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis type="number" tick={{ fontSize: 11 }} />
        <YAxis dataKey="country" type="category" tick={{ fontSize: 11 }} width={80} />
        <Tooltip />
        <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} name="Errors" />
      </BarChart>
    </ResponsiveContainer>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex h-[280px] items-center justify-center text-sm text-slate-400">
      {message}
    </div>
  );
}
