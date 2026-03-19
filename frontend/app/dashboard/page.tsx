"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Badge,
  Card,
  Metric,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Text,
  Title,
} from "@tremor/react";
import { ArrowUpRight, Brain, Gauge, Radar, Sparkles, Workflow } from "lucide-react";

type RiskStatus = "Green" | "Yellow" | "Red";

type RiskRow = {
  module: string;
  owner: string;
  complexity: string;
  busFactor: number;
  status: RiskStatus;
};

type AnalysisResponse = {
  similarity: number;
  similarity_components?: {
    semantic_score: number;
    keyword_overlap: number;
    contradiction_detected: boolean;
  };
  complexity: number;
  impact: "Low" | "Medium" | "High" | string;
  summary: string;
  relevance_insights?: {
    requirement_focus_terms: string[];
    code_signals: {
      functions: string[];
      files: string[];
    };
    overlap_terms: string[];
    relevance_reason: string;
    contradiction_detected?: boolean;
    contradiction_detail?: string;
  };
  developer_intelligence: {
    bus_factor: number;
    burnout_risk: string;
    hotspot_status: string;
    activity_log_count: number;
  };
  objective_coverage: {
    intake_ready: boolean;
    intent_mapping_score: number;
    effort_estimation_ready: boolean;
    contribution_insight_ready: boolean;
    explainability_ready: boolean;
  };
  baseline_requirements: Array<{
    name: string;
    status: string;
    detail: string;
  }>;
  challenge_matrix: Array<{
    name: string;
    status: string;
    detail: string;
  }>;
};

type HealthResponse = {
  status: string;
  model_loaded: boolean;
  server_time: string;
};

type DashboardData = {
  impactScore: number;
  riskRows: RiskRow[];
};

type AnalysisHistoryItem = {
  id: string;
  timestamp: string;
  requirement: string;
  codeDiff: string;
  similarity: number;
  complexity: number;
  impact: string;
};

const ANALYSIS_HISTORY_STORAGE_KEY = "devpulse.analysisHistory";
const MAX_HISTORY_ITEMS = 20;

const initialAnalysis: AnalysisResponse = {
  similarity: 0,
  similarity_components: {
    semantic_score: 0,
    keyword_overlap: 0,
    contradiction_detected: false,
  },
  complexity: 0,
  impact: "Low",
  summary: "Click Analyze to generate live AI insight from your backend.",
  relevance_insights: {
    requirement_focus_terms: [],
    code_signals: { functions: [], files: [] },
    overlap_terms: [],
    relevance_reason: "Run analysis to see requirement-to-code evidence.",
  },
  developer_intelligence: {
    bus_factor: 0,
    burnout_risk: "Low",
    hotspot_status: "Routine Module",
    activity_log_count: 0,
  },
  objective_coverage: {
    intake_ready: false,
    intent_mapping_score: 0,
    effort_estimation_ready: false,
    contribution_insight_ready: false,
    explainability_ready: false,
  },
  baseline_requirements: [],
  challenge_matrix: [],
};

const getStatusFromImpact = (impact: string): RiskStatus => {
  if (impact === "High") return "Red";
  if (impact === "Medium") return "Yellow";
  return "Green";
};

const getComplexityLabel = (complexity: number): string => {
  if (complexity > 8) return "High";
  if (complexity > 3) return "Medium";
  return "Low";
};

const buildDashboardData = (analysis: AnalysisResponse): DashboardData => {
  const impactScore = Math.max(0, Math.min(100, Math.round(analysis.similarity * 100)));
  const status = getStatusFromImpact(analysis.impact);
  const complexityLabel = getComplexityLabel(analysis.complexity);

  return {
    impactScore,
    riskRows: [
      {
        module: "Authentication Gateway",
        owner: "AI Analysis",
        complexity: complexityLabel,
        busFactor: status === "Red" ? 1 : status === "Yellow" ? 2 : 4,
        status,
      },
      {
        module: "Core Services",
        owner: "Platform Team",
        complexity: analysis.complexity > 10 ? "Medium" : "Low",
        busFactor: 3,
        status: analysis.complexity > 10 ? "Yellow" : "Green",
      },
      {
        module: "Delivery Pipeline",
        owner: "DevOps",
        complexity: "Low",
        busFactor: 4,
        status: "Green",
      },
    ],
  };
};

function getStatusColor(status: RiskStatus): "emerald" | "amber" | "rose" {
  if (status === "Green") return "emerald";
  if (status === "Yellow") return "amber";
  return "rose";
}

function isMeaningfulText(value: string): boolean {
  const cleaned = value.replace(/[^a-zA-Z0-9\s_]/g, " ").trim();
  if (!cleaned) return false;
  const tokens = cleaned.split(/\s+/).filter((token) => token.length >= 2);
  return tokens.length >= 3;
}

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function ExecutiveDashboardPage() {
  const [analysis, setAnalysis] = useState<AnalysisResponse>(initialAnalysis);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryItem[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [connectionLost, setConnectionLost] = useState<boolean>(false);
  const [inputWarning, setInputWarning] = useState<string>("");
  const [projectHealth, setProjectHealth] = useState<string>("Checking...");
  const [requirementInput, setRequirementInput] = useState<string>(
    "Improve authentication reliability and align implementation with requirements."
  );
  const [codeDiffInput, setCodeDiffInput] = useState<string>(
    "diff --git a/auth.py b/auth.py\n+ async def validate_jwt(token):\n+     return verify(token)"
  );

  const analysisData = useMemo(() => buildDashboardData(analysis), [analysis]);
  const hasValidRequirement = isMeaningfulText(requirementInput);
  const hasValidCodeDiff = isMeaningfulText(codeDiffInput);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(ANALYSIS_HISTORY_STORAGE_KEY);
      if (!stored) return;
      const parsed = JSON.parse(stored) as AnalysisHistoryItem[];
      if (Array.isArray(parsed)) {
        setAnalysisHistory(parsed);
      }
    } catch {
      setAnalysisHistory([]);
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(ANALYSIS_HISTORY_STORAGE_KEY, JSON.stringify(analysisHistory));
    } catch {
      // Ignore persistence failures in restricted browser contexts.
    }
  }, [analysisHistory]);

  useEffect(() => {
    const fetchProjectHealth = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/v1/health");
        if (!response.ok) {
          throw new Error(`Backend returned status ${response.status}`);
        }
        const health = (await response.json()) as HealthResponse;
        setProjectHealth(`${health.status.toUpperCase()}${health.model_loaded ? " / model loaded" : ""}`);
        setConnectionLost(false);
      } catch {
        setProjectHealth("OFFLINE");
        setConnectionLost(true);
      }
    };

    void fetchProjectHealth();
  }, []);

  const runAnalysis = async () => {
    if (!hasValidRequirement || !hasValidCodeDiff) {
      setInputWarning("Add a meaningful requirement and code diff before analyzing. A single '+' is not enough context.");
      return;
    }

    setInputWarning("");
    setIsAnalyzing(true);
    try {
      const response = await fetch("http://localhost:8000/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requirement: requirementInput,
          code_diff: codeDiffInput,
          commit_activity: [
            { author: "analyst", lines_changed: Math.max(1, codeDiffInput.split("\n").length * 2) },
            { author: "reviewer", lines_changed: 3 },
          ],
          activity_timestamps: [
            new Date().toISOString(),
            new Date(Date.now() - 86400000).toISOString(),
            new Date(Date.now() - 172800000).toISOString(),
          ],
          bug_frequency: 1,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned status ${response.status}`);
      }

      const result = (await response.json()) as AnalysisResponse;
      setAnalysis(result);
      setAnalysisHistory((prev) => {
        const next: AnalysisHistoryItem = {
          id: `${Date.now()}`,
          timestamp: new Date().toISOString(),
          requirement: requirementInput,
          codeDiff: codeDiffInput,
          similarity: result.similarity,
          complexity: result.complexity,
          impact: result.impact,
        };
        return [next, ...prev].slice(0, MAX_HISTORY_ITEMS);
      });
      setConnectionLost(false);
    } catch {
      setConnectionLost(true);
      setInputWarning("Unable to reach AI analysis service. Please check backend status.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute -left-28 top-20 h-72 w-72 rounded-full bg-rose-500/10 blur-3xl" />
      <div className="pointer-events-none absolute right-0 top-96 h-80 w-80 rounded-full bg-emerald-400/10 blur-3xl" />

      <motion.div
        initial="hidden"
        animate="visible"
        transition={{ staggerChildren: 0.08 }}
        className="space-y-6"
      >
        <motion.section variants={fadeIn} transition={{ duration: 0.45 }}>
          <Card className="relative overflow-hidden border border-zinc-800/90 bg-gradient-to-br from-zinc-950 to-zinc-900">
            <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-[11px] uppercase tracking-[0.32em] text-zinc-400">Developer Student Community</p>
                <Title className="mt-3 max-w-3xl text-3xl leading-tight text-zinc-100 sm:text-4xl">
                  AI-Driven Effort Estimation and Developer Intelligence System
                </Title>
              </div>
              <Badge color={connectionLost ? "rose" : "emerald"}>Project Health: {projectHealth}</Badge>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card className="border border-zinc-800 bg-zinc-950/60">
                <div className="flex items-center gap-2 text-zinc-300">
                  <Brain className="h-4 w-4 text-emerald-300" />
                  <Text>Similarity</Text>
                </div>
                <Metric className="mt-2 text-zinc-100">{Math.round(analysis.similarity * 100)}%</Metric>
              </Card>

              <Card className="border border-zinc-800 bg-zinc-950/60">
                <div className="flex items-center gap-2 text-zinc-300">
                  <Gauge className="h-4 w-4 text-emerald-300" />
                  <Text>Complexity</Text>
                </div>
                <Metric className="mt-2 text-zinc-100">{analysis.complexity}</Metric>
              </Card>

              <Card className="border border-zinc-800 bg-zinc-950/60">
                <div className="flex items-center gap-2 text-zinc-300">
                  <Sparkles className="h-4 w-4 text-emerald-300" />
                  <Text>Impact</Text>
                </div>
                <Metric className="mt-2 text-zinc-100">{analysis.impact}</Metric>
              </Card>
            </div>
          </Card>
        </motion.section>

        <motion.section variants={fadeIn} transition={{ duration: 0.45 }}>
          <Card className="border border-zinc-800 bg-zinc-900/80">
            <div className="mb-3 flex items-center gap-2">
              <Workflow className="h-4 w-4 text-emerald-300" />
              <Title>AI Analyzer</Title>
            </div>

            {connectionLost && (
              <div className="mb-3 rounded-md border border-rose-700/60 bg-rose-950/30 px-3 py-2 text-rose-200">
                <Text>Connection Lost to AI Brain</Text>
              </div>
            )}

            {inputWarning && (
              <div className="mb-3 rounded-md border border-amber-700/60 bg-amber-950/30 px-3 py-2 text-amber-200">
                <Text>{inputWarning}</Text>
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <div>
                <Text>Requirement</Text>
                <textarea
                  value={requirementInput}
                  onChange={(event) => setRequirementInput(event.target.value)}
                  rows={6}
                  className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-3 text-sm text-zinc-100 outline-none placeholder:text-zinc-500 focus:border-emerald-400"
                  placeholder="Describe business intent or ticket objective"
                />
              </div>

              <div>
                <Text>Code Diff</Text>
                <textarea
                  value={codeDiffInput}
                  onChange={(event) => setCodeDiffInput(event.target.value)}
                  rows={6}
                  className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-3 text-sm text-zinc-100 outline-none placeholder:text-zinc-500 focus:border-emerald-400"
                  placeholder="Paste code diff, commit slice, or implementation snippet"
                />
              </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => void runAnalysis()}
                disabled={isAnalyzing || !hasValidRequirement || !hasValidCodeDiff}
                className="inline-flex items-center gap-2 rounded-lg bg-emerald-400 px-4 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isAnalyzing ? "Analyzing..." : "Analyze"}
                <ArrowUpRight className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-3 rounded-md border border-zinc-800 bg-zinc-950/40 p-3">
              <Text>{analysis.summary}</Text>
              <div className="mt-2 space-y-1 text-xs text-zinc-400">
                <p>Relevance signal: {analysis.relevance_insights?.relevance_reason ?? "No relevance details returned."}</p>
                <p>
                  Requirement terms: {(analysis.relevance_insights?.requirement_focus_terms ?? []).slice(0, 6).join(", ") || "-"}
                </p>
                <p>Matched terms: {(analysis.relevance_insights?.overlap_terms ?? []).join(", ") || "-"}</p>
                <p>
                  Code signals: {(analysis.relevance_insights?.code_signals.functions ?? []).slice(0, 4).join(", ") || "-"}
                </p>
                <p>
                  Score components: semantic {(analysis.similarity_components?.semantic_score ?? 0).toFixed(2)} | keyword overlap {(analysis.similarity_components?.keyword_overlap ?? 0).toFixed(2)}
                </p>
                {analysis.relevance_insights?.contradiction_detected && (
                  <p className="text-rose-300">
                    Intent contradiction: {analysis.relevance_insights?.contradiction_detail ?? "Requirement and code actions conflict."}
                  </p>
                )}
              </div>
            </div>
          </Card>
        </motion.section>

        <motion.section variants={fadeIn} transition={{ duration: 0.45 }}>
          <Card className="border border-zinc-800 bg-zinc-900">
            <div className="mb-4 flex items-center gap-2">
              <Radar className="h-4 w-4 text-emerald-300" />
              <Title>Risk Radar</Title>
            </div>
            <Text>AI-assisted hotspot mapping across critical modules.</Text>

            <Table className="mt-4">
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Module</TableHeaderCell>
                  <TableHeaderCell>Owner</TableHeaderCell>
                  <TableHeaderCell>Complexity</TableHeaderCell>
                  <TableHeaderCell>Bus Factor</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {analysisData.riskRows.map((row) => (
                  <TableRow key={row.module}>
                    <TableCell>{row.module}</TableCell>
                    <TableCell>{row.owner}</TableCell>
                    <TableCell>{row.complexity}</TableCell>
                    <TableCell>{row.busFactor}</TableCell>
                    <TableCell>
                      <Badge color={getStatusColor(row.status)}>{row.status}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </motion.section>

        <motion.section variants={fadeIn} transition={{ duration: 0.45 }}>
          <Card className="border border-zinc-800 bg-zinc-900">
            <div className="mb-4 flex items-center gap-2">
              <Title>Analysis History</Title>
            </div>
            {analysisHistory.length === 0 ? (
              <Text>No analysis history yet. Run Analyze to store requirement, diff, and metrics with timestamp.</Text>
            ) : (
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>Timestamp</TableHeaderCell>
                    <TableHeaderCell>Requirement</TableHeaderCell>
                    <TableHeaderCell>Code Diff</TableHeaderCell>
                    <TableHeaderCell>Similarity</TableHeaderCell>
                    <TableHeaderCell>Complexity</TableHeaderCell>
                    <TableHeaderCell>Impact</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {analysisHistory.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{new Date(item.timestamp).toLocaleString()}</TableCell>
                      <TableCell className="max-w-[220px] truncate" title={item.requirement}>{item.requirement}</TableCell>
                      <TableCell className="max-w-[260px] truncate" title={item.codeDiff}>{item.codeDiff}</TableCell>
                      <TableCell>{Math.round(item.similarity * 100)}%</TableCell>
                      <TableCell>{item.complexity}</TableCell>
                      <TableCell>{item.impact}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </motion.section>

      </motion.div>
    </div>
  );
}
