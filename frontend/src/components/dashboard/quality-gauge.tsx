"use client";

import { getQualityColor, getQualityLabel } from "@/lib/utils";

interface QualityGaugeProps {
  score: number;
  size?: number;
}

export function QualityGauge({ score, size = 180 }: QualityGaugeProps) {
  const color = getQualityColor(score);
  const label = getQualityLabel(score);
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox="0 0 180 180">
        <circle cx="90" cy="90" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="12" />
        <circle
          cx="90" cy="90" r={radius} fill="none"
          stroke={color} strokeWidth="12" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          transform="rotate(-90 90 90)"
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
        <text x="90" y="85" textAnchor="middle" className="fill-slate-900 text-3xl font-bold" fontSize="32">
          {Math.round(score)}
        </text>
        <text x="90" y="108" textAnchor="middle" fill="#64748b" fontSize="12">
          /100
        </text>
      </svg>
      <span className="mt-2 text-sm font-semibold" style={{ color }}>{label}</span>
    </div>
  );
}
