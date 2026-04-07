"use client";

import { useState, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import {
  Database,
  Zap,
  TrendingUp,
  Users,
  Award,
  Shield,
  Loader2,
  Play,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Activity,
  Target,
  BarChart3,
  Cpu,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import {
  postDatasetGenerate,
  fetchATE,
  fetchModels,
  fetchSegments,
  fetchRecommendations,
  type AnalysisATEResponse,
  type AnalysisModelsResponse,
  type AnalysisSegmentsResponse,
  type AnalysisRecommendationsResponse,
  type DatasetGenerateResponse,
} from "@/lib/primelift-api";
import { cn } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

// ─── Types ──────────────────────────────────────────────────────────────────

type StepId = "dataset" | "ate" | "models" | "segments" | "recommendations";
type StepStatus = "pending" | "running" | "done" | "error";
type DashboardPhase = "idle" | "running" | "ready" | "error";

type AnalysisBundle = {
  dataset: DatasetGenerateResponse;
  ate: AnalysisATEResponse;
  models: AnalysisModelsResponse;
  segments: AnalysisSegmentsResponse;
  recommendations: AnalysisRecommendationsResponse;
};

// ─── Constants ──────────────────────────────────────────────────────────────

const STEP_META: Array<{ id: StepId; label: string; icon: React.ElementType }> = [
  { id: "dataset", label: "Generate Dataset", icon: Database },
  { id: "ate", label: "Compute ATE & CI", icon: Activity },
  { id: "models", label: "Load Model Registry", icon: Cpu },
  { id: "segments", label: "Segment Analysis", icon: BarChart3 },
  { id: "recommendations", label: "Policy Recommendations", icon: Target },
];

const INITIAL_STEPS: Record<StepId, StepStatus> = {
  dataset: "pending",
  ate: "pending",
  models: "pending",
  segments: "pending",
  recommendations: "pending",
};

const BUDGET_COLORS = ["#22d3ee", "#06b6d4", "#0891b2", "#0e7490", "#155e75", "#164e63"];

const MODEL_LABELS: Record<string, string> = {
  drlearner_conversion: "DRLearner",
  xlearner_conversion: "XLearner",
  causal_forest_conversion: "CausalForest",
  drlearner_revenue: "DRLearner Revenue",
  drpolicytree_conversion: "DRPolicyTree",
  drpolicyforest_conversion: "DRPolicyForest",
};

// ─── Formatters ─────────────────────────────────────────────────────────────

function pp(v: number | null | undefined, digits = 2) {
  if (v == null) return "n/a";
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(digits)}pp`;
}

function modelLabel(name: string) {
  return MODEL_LABELS[name] ?? name;
}

function pct(v: number) {
  return `${(v * 100).toFixed(1)}%`;
}

// ─── Chart Tooltip ───────────────────────────────────────────────────────────

function ChartTooltip({
  active,
  payload,
  label,
  format,
}: {
  active?: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload?: ReadonlyArray<Record<string, any>>;
  label?: string | number;
  format?: (v: number) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card/95 px-3 py-2 shadow-xl backdrop-blur-sm">
      {label != null && (
        <p className="mb-1 text-[11px] font-medium text-muted-foreground">{label}</p>
      )}
      {payload.map((p, i) => {
        const v = typeof p.value === "number" ? p.value : 0;
        return (
          <p key={i} className="text-sm font-medium tabular-nums" style={{ color: (p.color as string) ?? "#22d3ee" }}>
            {format ? format(v) : v.toFixed(4)}
          </p>
        );
      })}
    </div>
  );
}

// ─── KPI Card ────────────────────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  sub,
  icon: Icon,
  accent = false,
}: {
  label: string;
  value: string;
  sub: string;
  icon: React.ElementType;
  accent?: boolean;
}) {
  return (
    <Card className={cn(
      "border-border/50 bg-card/80 backdrop-blur-sm transition-all hover:border-border",
      accent && "border-cyan-500/20 shadow-[0_0_30px_rgba(6,182,212,0.06)]"
    )}>
      <CardContent className="pt-5 pb-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-cyan-500/10">
            <Icon className="h-3 w-3 text-cyan-400" />
          </div>
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{label}</span>
        </div>
        <p className="text-2xl font-light tracking-tight text-white">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{sub}</p>
      </CardContent>
    </Card>
  );
}

// ─── Pipeline Step ───────────────────────────────────────────────────────────

function PipelineStep({
  label,
  status,
  icon: Icon,
}: {
  label: string;
  status: StepStatus;
  icon: React.ElementType;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border px-4 py-3 transition-all duration-500",
        status === "done" && "border-cyan-500/20 bg-cyan-500/5",
        status === "running" && "border-cyan-400/40 bg-cyan-400/8",
        status === "pending" && "border-border/40 bg-card/40",
        status === "error" && "border-destructive/30 bg-destructive/5",
      )}
    >
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-md",
          status === "done" && "bg-cyan-500/10",
          status === "running" && "bg-cyan-400/15",
          status === "pending" && "bg-muted",
          status === "error" && "bg-destructive/10",
        )}
      >
        {status === "running" && <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-400" />}
        {status === "done" && <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" />}
        {status === "error" && <AlertCircle className="h-3.5 w-3.5 text-destructive" />}
        {status === "pending" && <Icon className="h-3.5 w-3.5 text-muted-foreground/50" />}
      </div>
      <span
        className={cn(
          "text-sm",
          status === "done" && "font-medium text-cyan-300",
          status === "running" && "font-medium text-white",
          status === "pending" && "text-muted-foreground/60",
          status === "error" && "font-medium text-destructive",
        )}
      >
        {label}
      </span>
      {status === "done" && (
        <span className="ml-auto text-[10px] font-medium uppercase tracking-wider text-cyan-500/70">Done</span>
      )}
      {status === "running" && (
        <span className="ml-auto text-[10px] font-medium uppercase tracking-wider text-cyan-400">Running</span>
      )}
    </div>
  );
}

// ─── Idle Panel ──────────────────────────────────────────────────────────────

function IdlePanel({
  rows,
  seed,
  onRowsChange,
  onSeedChange,
  onRun,
}: {
  rows: number;
  seed: number;
  onRowsChange: (v: number) => void;
  onSeedChange: (v: number) => void;
  onRun: () => void;
}) {
  return (
    <div className="flex min-h-[calc(100vh-60px)] flex-col items-center justify-center px-4 py-16">
      <div className="relative w-full max-w-md">
        {/* Badge */}
        <div className="mb-8 flex justify-center">
          <Badge variant="outline" className="gap-1.5 border-cyan-500/20 bg-cyan-500/5 px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-cyan-400">
            <Sparkles className="h-3 w-3" />
            Causal Uplift Intelligence
          </Badge>
        </div>

        <h1 className="mb-3 text-center text-4xl font-extralight tracking-tight text-white">
          Prime<span className="font-light text-cyan-400">Lift</span>
        </h1>
        <p className="mb-10 text-center text-sm font-light text-muted-foreground">
          Generate your dataset and run the full causal ML pipeline.
        </p>

        {/* Config card */}
        <Card className="border-border/40 bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Dataset Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-[11px] font-medium text-muted-foreground">
                  Dataset Size
                </label>
                <select
                  value={rows}
                  onChange={(e) => onRowsChange(Number(e.target.value))}
                  className="w-full rounded-lg border border-border/60 bg-input px-3 py-2.5 text-sm text-foreground outline-none transition focus:border-cyan-500/40 focus:ring-1 focus:ring-cyan-500/20"
                >
                  <option value={10000}>10,000 rows</option>
                  <option value={50000}>50,000 rows</option>
                  <option value={100000}>100,000 rows (default)</option>
                  <option value={200000}>200,000 rows</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-[11px] font-medium text-muted-foreground">
                  Random Seed
                </label>
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => onSeedChange(Number(e.target.value))}
                  className="w-full rounded-lg border border-border/60 bg-input px-3 py-2.5 text-sm text-foreground outline-none transition focus:border-cyan-500/40 focus:ring-1 focus:ring-cyan-500/20"
                />
              </div>
            </div>

            <button
              onClick={onRun}
              className="group flex w-full items-center justify-center gap-2.5 rounded-lg bg-cyan-500 px-5 py-3 text-sm font-medium text-slate-950 transition-all hover:bg-cyan-400 active:scale-[0.98]"
            >
              <Play className="h-3.5 w-3.5" />
              Generate & Analyse
            </button>
          </CardContent>
        </Card>

        {/* Feature pills */}
        <div className="mt-6 flex flex-wrap justify-center gap-1.5">
          {[
            "Bootstrap CI",
            "Causal Forest",
            "DRLearner",
            "Policy Optimisation",
            "Segment Rollup",
          ].map((f) => (
            <span
              key={f}
              className="rounded-md border border-border/30 bg-muted/30 px-2.5 py-1 text-[10px] font-medium text-muted-foreground/60"
            >
              {f}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Running Panel ───────────────────────────────────────────────────────────

function RunningPanel({ steps }: { steps: Record<StepId, StepStatus> }) {
  const doneCount = Object.values(steps).filter((s) => s === "done").length;
  const total = STEP_META.length;
  const progress = (doneCount / total) * 100;

  return (
    <div className="flex min-h-[calc(100vh-60px)] flex-col items-center justify-center px-4 py-16">
      <div className="relative w-full max-w-lg">
        <div className="mb-8 text-center">
          <p className="text-[11px] font-medium uppercase tracking-wider text-cyan-500">Pipeline running</p>
          <h2 className="mt-2 text-2xl font-light tracking-tight text-white">
            Analysing your dataset
          </h2>
          <p className="mt-1.5 text-sm text-muted-foreground">
            {doneCount} of {total} steps complete
          </p>
        </div>

        {/* Progress bar */}
        <div className="mb-5 h-0.5 w-full overflow-hidden rounded-full bg-border/30">
          <div
            className="h-full rounded-full bg-cyan-400 transition-all duration-700"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="space-y-1.5">
          {STEP_META.map(({ id, label, icon }) => (
            <PipelineStep key={id} label={label} status={steps[id]} icon={icon} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Decile Chart ────────────────────────────────────────────────────────────

function DecileChart({ deciles }: { deciles: AnalysisSegmentsResponse["deciles"] }) {
  const data = deciles.map((d) => ({
    name: `D${d.decile_rank}`,
    ate: d.observed_ate == null ? 0 : parseFloat((d.observed_ate * 100).toFixed(3)),
    positive: d.observed_ate != null && d.observed_ate >= 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} unit="pp" />
        <Tooltip
          content={(props) => (
            <ChartTooltip
              {...props}
              format={(v) => `${v >= 0 ? "+" : ""}${v.toFixed(3)}pp`}
            />
          )}
        />
        <ReferenceLine y={0} stroke="rgba(148,163,184,0.15)" strokeWidth={1} />
        <Bar dataKey="ate" radius={[3, 3, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={index}
              fill={entry.positive ? "#22d3ee" : "#f43f5e"}
              fillOpacity={0.8}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ─── Budget Pie ───────────────────────────────────────────────────────────────

function BudgetPie({
  segments,
}: {
  segments: AnalysisRecommendationsResponse["report"]["prioritized_segments"];
}) {
  const data = segments.map((s) => ({
    name: s.segment,
    value: parseFloat((s.budget_share * 100).toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={58}
          outerRadius={88}
          paddingAngle={2}
          dataKey="value"
          strokeWidth={0}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={BUDGET_COLORS[i % BUDGET_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          content={(props) => (
            <ChartTooltip {...props} format={(v) => `${v.toFixed(1)}%`} />
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

// ─── Segment Bars ─────────────────────────────────────────────────────────────

function SegmentBars({
  cohorts,
  color,
}: {
  cohorts: Array<{ group_value: string; mean_predicted_effect: number; observed_ate: number }>;
  color: "cyan" | "rose";
}) {
  if (!cohorts.length) {
    return <p className="py-8 text-center text-sm text-muted-foreground">No data available</p>;
  }

  const max = Math.max(...cohorts.map((c) => Math.abs(c.mean_predicted_effect)));

  return (
    <div className="space-y-3">
      {cohorts.slice(0, 5).map((c) => {
        const barPct = max > 0 ? Math.abs(c.mean_predicted_effect) / max : 0;
        return (
          <div key={c.group_value}>
            <div className="mb-1.5 flex items-center justify-between gap-2">
              <span className="truncate text-[13px] font-light text-foreground/80">{c.group_value}</span>
              <span
                className={cn(
                  "shrink-0 text-xs font-medium tabular-nums",
                  color === "cyan" ? "text-cyan-400" : "text-rose-400",
                )}
              >
                {pp(c.mean_predicted_effect)}
              </span>
            </div>
            <div className="h-1 w-full overflow-hidden rounded-full bg-border/20">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-700",
                  color === "cyan"
                    ? "bg-cyan-400/70"
                    : "bg-rose-400/70",
                )}
                style={{ width: `${barPct * 100}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Ready Dashboard ──────────────────────────────────────────────────────────

function ReadyDashboard({
  data,
  onReset,
}: {
  data: AnalysisBundle;
  onReset: () => void;
}) {
  const { ate, models, segments, recommendations } = data;

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-8 sm:px-6 lg:px-10">
      {/* ── Header ── */}
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-extralight tracking-tight text-white">
              Prime<span className="font-light text-cyan-400">Lift</span>
            </h1>
            <Separator orientation="vertical" className="h-5 bg-border/30" />
            <Badge variant="outline" className="border-emerald-500/20 bg-emerald-500/8 text-[10px] font-medium text-emerald-400">
              Live
            </Badge>
          </div>
          <p className="mt-1 text-xs font-light text-muted-foreground">
            {ate.row_count.toLocaleString()} rows · {modelLabel(models.conversion_champion_model_name)} champion · Seed {data.dataset.seed}
          </p>
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-2 rounded-lg border border-border/50 bg-card/50 px-4 py-2 text-xs font-medium text-muted-foreground transition hover:border-cyan-500/30 hover:text-cyan-400"
        >
          <RefreshCw className="h-3 w-3" />
          Re-run
        </button>
      </div>

      {/* ── KPIs ── */}
      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Baseline ATE"
          value={pp(ate.result.ate)}
          sub={`95% CI: ${pp(ate.result.ci_lower)} → ${pp(ate.result.ci_upper)}`}
          icon={TrendingUp}
          accent
        />
        <KpiCard
          label="Champion Model"
          value={modelLabel(models.conversion_champion_model_name)}
          sub={`Split: ${models.comparison_split}`}
          icon={Award}
        />
        <KpiCard
          label="Policy Champion"
          value={modelLabel(recommendations.policy_champion_model_name)}
          sub={`Value: ${recommendations.policy_champion_value.toFixed(4)}`}
          icon={Target}
        />
        <KpiCard
          label="Target Users"
          value={recommendations.top_target_user_count.toLocaleString()}
          sub={`${recommendations.prioritized_segment_count} priority segments`}
          icon={Users}
        />
      </div>

      {/* ── Row 1: Decile Chart + Budget Pie ── */}
      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <Card className="border-border/40 bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-foreground/90">Uplift by Decile</CardTitle>
            <CardDescription className="text-xs">Observed ATE per model decile rank</CardDescription>
          </CardHeader>
          <CardContent>
            <DecileChart deciles={segments.deciles} />
            <div className="mt-3 flex gap-4 text-[11px] text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-cyan-400" />
                Positive lift
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-rose-400" />
                Negative lift
              </span>
              <span className="ml-auto tabular-nums">
                Top decile gain: <span className="font-medium text-cyan-400">{pp(segments.top_decile_gain_over_overall_ate)}</span>
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/40 bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-foreground/90">Budget Allocation</CardTitle>
            <CardDescription className="text-xs">Recommended budget share per segment</CardDescription>
          </CardHeader>
          <CardContent>
            {recommendations.report.prioritized_segments.length > 0 ? (
              <>
                <BudgetPie segments={recommendations.report.prioritized_segments} />
                <div className="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1.5">
                  {recommendations.report.prioritized_segments.slice(0, 6).map((s, i) => (
                    <div key={s.segment} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                      <span
                        className="inline-block h-2 w-2 rounded-full"
                        style={{ background: BUDGET_COLORS[i % BUDGET_COLORS.length] }}
                      />
                      {s.segment} <span className="text-muted-foreground/50">({pct(s.budget_share)})</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="flex h-48 items-center justify-center text-sm text-muted-foreground">
                No prioritized segments available
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Row 2: Top Segments + Suppression ── */}
      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <Card className="border-border/40 bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-foreground/90">Top Persuadable Cohorts</CardTitle>
            <CardDescription className="text-xs">Highest predicted treatment effect</CardDescription>
          </CardHeader>
          <CardContent>
            <SegmentBars cohorts={segments.top_persuadable_cohorts} color="cyan" />
          </CardContent>
        </Card>

        <Card className="border-border/40 bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-foreground/90">Suppression Candidates</CardTitle>
            <CardDescription className="text-xs">Cohorts with negative predicted effect</CardDescription>
          </CardHeader>
          <CardContent>
            <SegmentBars cohorts={segments.suppression_candidates} color="rose" />
          </CardContent>
        </Card>
      </div>

      {/* ── Row 3: Validation + Recommendation ── */}
      <div className="mb-6 grid gap-4 lg:grid-cols-[1fr_1.4fr]">
        {/* Validation */}
        <Card className="border-border/40 bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-foreground/90">Model Validation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between rounded-md bg-muted/30 px-3 py-2.5">
              <span className="text-xs text-muted-foreground">Verdict</span>
              <span className="text-xs font-medium text-cyan-400">
                {segments.validation_verdict}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-md bg-muted/30 px-3 py-2.5">
              <span className="text-xs text-muted-foreground">Monotonicity breaks</span>
              <span className="text-xs font-medium tabular-nums text-foreground/80">
                {segments.monotonicity_break_count}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-md bg-muted/30 px-3 py-2.5">
              <span className="text-xs text-muted-foreground">Conc. ratio</span>
              <span className="text-xs font-medium tabular-nums text-foreground/80">
                {segments.uplift_concentration_ratio?.toFixed(3) ?? "n/a"}
              </span>
            </div>
            <p className="rounded-md border border-border/30 bg-muted/15 px-3 py-2.5 text-xs font-light leading-5 text-muted-foreground">
              {segments.validation_reason}
            </p>
          </CardContent>
        </Card>

        {/* Recommendation summary */}
        <Card className="border-cyan-500/15 bg-gradient-to-br from-card/80 to-card/40 backdrop-blur-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-3.5 w-3.5 text-cyan-400" />
              <CardTitle className="text-sm font-medium text-foreground/90">Policy Recommendation</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-[15px] font-light leading-7 text-foreground/80">
              {recommendations.final_action_summary}
            </p>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-muted/20 px-4 py-3">
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Target Users</p>
                <p className="mt-1 text-xl font-light tabular-nums text-white">
                  {recommendations.top_target_user_count.toLocaleString()}
                </p>
              </div>
              <div className="rounded-lg bg-muted/20 px-4 py-3">
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Suppress Users</p>
                <p className="mt-1 text-xl font-light tabular-nums text-white">
                  {recommendations.top_suppress_user_count.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Prioritised segments */}
            {recommendations.report.prioritized_segments.length > 0 && (
              <div className="mt-5">
                <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Prioritised segments
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {recommendations.report.prioritized_segments.map((s) => (
                    <Badge
                      key={s.segment}
                      variant="outline"
                      className="gap-0.5 border-cyan-500/15 bg-cyan-500/5 text-[11px] font-normal text-cyan-300"
                    >
                      <ChevronRight className="h-2.5 w-2.5" />
                      {s.segment}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Suppressed */}
            {recommendations.report.suppressed_segments.length > 0 && (
              <div className="mt-3">
                <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Suppressed
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {recommendations.report.suppressed_segments.map((s) => (
                    <Badge
                      key={s.segment}
                      variant="outline"
                      className="border-rose-500/15 bg-rose-500/5 text-[11px] font-normal text-rose-400"
                    >
                      {s.segment}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── ATE Detail strip ── */}
      <Card className="mb-6 border-border/40 bg-card/60 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-foreground/90">Average Treatment Effect — Full Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2.5 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
            {[
              { label: "ATE", value: pp(ate.result.ate) },
              { label: "Treated mean", value: pp(ate.result.treated_mean) },
              { label: "Control mean", value: pp(ate.result.control_mean) },
              { label: "Relative lift", value: `${((ate.result.relative_lift ?? 0) * 100).toFixed(2)}%` },
              { label: "CI lower", value: pp(ate.result.ci_lower) },
              { label: "CI upper", value: pp(ate.result.ci_upper) },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-md bg-muted/20 px-3 py-2.5">
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
                <p className="mt-1 text-base font-light tabular-nums text-cyan-300">{value}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <p className="text-center text-[11px] font-light text-muted-foreground/40">
        PrimeLift · London Causal ML · {new Date().getFullYear()}
      </p>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function PrimeDashboard() {
  const [phase, setPhase] = useState<DashboardPhase>("idle");
  const [steps, setSteps] = useState<Record<StepId, StepStatus>>(INITIAL_STEPS);
  const [bundle, setBundle] = useState<AnalysisBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState(100_000);
  const [seed, setSeed] = useState(42);

  function markStep(id: StepId, status: StepStatus) {
    setSteps((prev) => ({ ...prev, [id]: status }));
  }

  const handleRun = useCallback(async () => {
    setPhase("running");
    setError(null);
    setSteps(INITIAL_STEPS);

    try {
      markStep("dataset", "running");
      const dataset = await postDatasetGenerate(rows, seed);
      markStep("dataset", "done");

      markStep("ate", "running");
      markStep("models", "running");
      markStep("segments", "running");
      markStep("recommendations", "running");

      const [ate, models, segments, recommendations] = await Promise.all([
        fetchATE(30).then((r) => { markStep("ate", "done"); return r; }),
        fetchModels().then((r) => { markStep("models", "done"); return r; }),
        fetchSegments().then((r) => { markStep("segments", "done"); return r; }),
        fetchRecommendations().then((r) => { markStep("recommendations", "done"); return r; }),
      ]);

      setBundle({ dataset, ate, models, segments, recommendations });
      setPhase("ready");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(msg);
      setPhase("error");
    }
  }, [rows, seed]);

  const handleReset = useCallback(() => {
    setPhase("idle");
    setBundle(null);
    setError(null);
    setSteps(INITIAL_STEPS);
  }, []);

  if (phase === "idle") {
    return (
      <IdlePanel
        rows={rows}
        seed={seed}
        onRowsChange={setRows}
        onSeedChange={setSeed}
        onRun={handleRun}
      />
    );
  }

  if (phase === "running") {
    return <RunningPanel steps={steps} />;
  }

  if (phase === "error") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-4">
        <Card className="w-full max-w-md border-destructive/20 bg-card/60 text-center">
          <CardContent className="pt-8 pb-8">
            <AlertCircle className="mx-auto mb-4 h-8 w-8 text-destructive/80" />
            <h2 className="text-lg font-light text-white">Pipeline failed</h2>
            <p className="mt-2 text-sm text-muted-foreground">{error}</p>
            <p className="mt-2 text-xs text-muted-foreground/60">
              Make sure the FastAPI backend is running at{" "}
              <code className="font-mono text-muted-foreground">http://127.0.0.1:8001</code>
            </p>
            <button
              onClick={handleReset}
              className="mt-6 rounded-lg bg-destructive/10 px-5 py-2 text-sm font-medium text-destructive transition hover:bg-destructive/20"
            >
              Try Again
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (phase === "ready" && bundle) {
    return <ReadyDashboard data={bundle} onReset={handleReset} />;
  }

  return null;
}
