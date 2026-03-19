"use client";

import { Cpu, Shield, Zap, Info, type LucideIcon } from "lucide-react";

export type InsightType = "security" | "performance" | "architecture" | "general";

export type Insight = {
  id: string;
  type: InsightType;
  headline: string;
  summary: string;
  timestamp: Date | string;
};

type InsightCardProps = {
  insight: Insight;
};

const TYPE_META: Record<InsightType, { icon: LucideIcon; color: string; bg: string }> = {
  security: {
    icon: Shield,
    color: "text-emerald-400",
    bg: "bg-emerald-400/10",
  },
  performance: {
    icon: Zap,
    color: "text-amber-400",
    bg: "bg-amber-400/10",
  },
  architecture: {
    icon: Cpu,
    color: "text-blue-400",
    bg: "bg-blue-400/10",
  },
  general: {
    icon: Info,
    color: "text-zinc-400",
    bg: "bg-zinc-400/10",
  },
};

function timeAgo(value: Date | string): string {
  const date = typeof value === "string" ? new Date(value) : value;
  const diffSeconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (diffSeconds < 60) return `${diffSeconds}s ago`;
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

function InsightCard({ insight }: InsightCardProps) {
  const meta = TYPE_META[insight.type] ?? TYPE_META.general;
  const Icon = meta.icon;

  return (
    <div className="group flex gap-3 rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 transition-colors duration-150 hover:border-zinc-600 hover:bg-zinc-800">
      <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${meta.bg}`}>
        <Icon className={`h-4 w-4 ${meta.color}`} />
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-zinc-100">{insight.headline}</p>
        <p className="mt-0.5 text-xs leading-relaxed text-zinc-400">{insight.summary}</p>
        <p className="mt-1.5 text-[11px] text-zinc-500">{timeAgo(insight.timestamp)}</p>
      </div>
    </div>
  );
}

type IntelligenceFeedProps = {
  insights: Insight[];
  className?: string;
};

export default function IntelligenceFeed({ insights, className = "" }: IntelligenceFeedProps) {
  return (
    <div className={`flex flex-col ${className}`}>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-100">AI Intelligence Feed</h2>
        <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-[11px] text-zinc-400">
          {insights.length} insights
        </span>
      </div>

      <div className="h-[420px] space-y-2 overflow-y-auto pr-1 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-zinc-700">
        {insights.length === 0 ? (
          <p className="py-8 text-center text-sm text-zinc-500">No insights yet.</p>
        ) : (
          insights.map((insight) => <InsightCard key={insight.id} insight={insight} />)
        )}
      </div>
    </div>
  );
}
