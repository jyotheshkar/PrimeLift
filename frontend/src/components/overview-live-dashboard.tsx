"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { MetricCard } from "@/components/metric-card";
import { SectionCard } from "@/components/section-card";
import {
  fetchOverviewBundle,
  type AnalysisRecommendationsResponse,
  type AnalysisSegmentsResponse,
} from "@/lib/primelift-api";
import { overviewSnapshot } from "@/lib/overview-data";

type OverviewSourceMode = "connecting" | "live" | "fallback";

type OverviewMetric = {
  label: string;
  value: string;
  detail: string;
  accent: "teal" | "amber" | "slate" | "coral";
};

type OverviewTopSegment = {
  name: string;
  uplift: number;
  budget: number;
};

type OverviewSuppressionWatch = {
  name: string;
  signal: string;
  note: string;
};

type OverviewRecommendation = {
  summary: string;
  targetUsers: number;
  suppressUsers: number;
  source: string;
};

type OverviewReadinessItem = {
  phase: string;
  item: string;
  status: string;
  tone: "ready" | "live" | "missing";
};

type OverviewViewModel = {
  headline: {
    label: string;
    title: string;
    description: string;
  };
  statusBadge: {
    label: string;
    tone: OverviewSourceMode;
  };
  kpis: OverviewMetric[];
  systemState: {
    policyChampion: string;
    policyValue: string;
    validationVerdict: string;
    testSplit: string;
    note: string;
    stance: string;
  };
  topSegments: OverviewTopSegment[];
  suppressionWatch: OverviewSuppressionWatch[];
  recommendation: OverviewRecommendation;
  readiness: OverviewReadinessItem[];
  nextUp: string[];
};

type OverviewState = {
  mode: OverviewSourceMode;
  data: OverviewViewModel;
  error: string | null;
};

function formatBarWidth(value: number) {
  return `${Math.max(18, Math.min(value * 12, 100))}%`;
}

function formatPercentagePoint(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}pp`;
}

function formatEffectAsPercentagePoints(value: number | null) {
  if (value === null) {
    return "n/a";
  }

  return formatPercentagePoint(value * 100);
}

function formatBudgetShare(share: number) {
  return `${(share * 100).toFixed(1)}%`;
}

function formatModelLabel(modelName: string) {
  const labelMap: Record<string, string> = {
    drlearner_conversion: "DRLearner",
    xlearner_conversion: "XLearner",
    causal_forest_conversion: "CausalForestDML",
    drlearner_revenue: "DRLearner Revenue",
    drpolicytree_conversion: "DRPolicyTree",
    drpolicyforest_conversion: "DRPolicyForest",
  };

  return labelMap[modelName] ?? modelName;
}

function describeSuppressionSignal(groupColumn: string) {
  if (groupColumn === "segment") {
    return "Segment-level holdout effect is negative. Keep it out of the priority pool.";
  }

  if (groupColumn === "channel") {
    return "Channel-level response is weak on holdout traffic. Deprioritize this entry path.";
  }

  if (groupColumn === "london_borough") {
    return "Local cohort response is under baseline. Treat this geography as a watch zone.";
  }

  return "Observed holdout response is weak for this cohort.";
}

function createFallbackViewModel(mode: OverviewSourceMode, error: string | null): OverviewViewModel {
  return {
    headline: {
      label: "London causal decision engine",
      title: overviewSnapshot.headline.title,
      description:
        mode === "connecting"
          ? "Connecting to the local FastAPI backend. Until it responds, the screen uses the saved Phase 7 artifact snapshot."
          : "The live backend could not be reached, so this screen is using the saved Phase 7 artifact snapshot instead of live API values.",
    },
    statusBadge: {
      label: mode === "connecting" ? "Connecting API" : "Snapshot fallback",
      tone: mode,
    },
    kpis: [...overviewSnapshot.kpis],
    systemState: {
      ...overviewSnapshot.systemState,
      stance:
        error === null
          ? "This screen will switch to live backend values as soon as the API responds."
          : `Snapshot mode is active because the API request failed: ${error}`,
    },
    topSegments: [...overviewSnapshot.topSegments],
    suppressionWatch: [...overviewSnapshot.suppressionWatch],
    recommendation: {
      ...overviewSnapshot.recommendation,
      source:
        mode === "connecting"
          ? "Saved Phase 7 overview snapshot while API connection initializes"
          : "Saved Phase 7 overview snapshot because the API is unavailable",
    },
    readiness: overviewSnapshot.readiness.map((item) => ({
      ...item,
      tone: "ready",
    })),
    nextUp: [
      "Integrate the uplift insights screen with the Phase 4 API endpoints.",
      "Integrate the recommendations screen with the Phase 5 closeout endpoint.",
      "Integrate the dataset and model panel with live dataset and registry responses.",
    ],
  };
}

function selectTopSegment(
  segments: AnalysisSegmentsResponse,
  recommendations: AnalysisRecommendationsResponse,
) {
  const segmentReport = segments.reports.find((report) => report.group_column === "segment");
  const topObservedSegment = segmentReport?.results.reduce<
    { group_value: string; observed_ate: number | null } | null
  >((best, current) => {
    if (current.observed_ate === null) {
      return best;
    }

    if (best === null || (best.observed_ate ?? Number.NEGATIVE_INFINITY) < current.observed_ate) {
      return current;
    }

    return best;
  }, null);
  const topBudgetSegment = recommendations.report.prioritized_segments[0];

  return {
    segmentName: topObservedSegment?.group_value ?? topBudgetSegment?.segment ?? "Unavailable",
    observedAte: topObservedSegment?.observed_ate ?? null,
    topBudgetSegment,
  };
}

function createLiveViewModel(
  bundle: Awaited<ReturnType<typeof fetchOverviewBundle>>,
): OverviewViewModel {
  const topSegment = selectTopSegment(bundle.segments, bundle.recommendations);
  const prioritizedSegments = bundle.recommendations.report.prioritized_segments.slice(0, 4);
  const suppressionCandidates = bundle.segments.suppression_candidates.slice(0, 3);

  return {
    headline: {
      label: "Live London causal decision engine",
      title: "PrimeLift AI is now reading live model outputs from the local FastAPI backend.",
      description:
        "This overview is powered by the Phase 6 analysis endpoints. The cards below reflect the current saved artifacts and recommendation state instead of a hard-coded snapshot.",
    },
    statusBadge: {
      label: "Live API connected",
      tone: "live",
    },
    kpis: [
      {
        label: "Baseline ATE",
        value: formatEffectAsPercentagePoints(bundle.ate.result.ate),
        detail: "Live conversion lift from the saved London experiment dataset.",
        accent: "teal",
      },
      {
        label: "Champion Model",
        value: formatModelLabel(bundle.models.conversion_champion_model_name),
        detail: `Current holdout winner from the ${bundle.models.comparison_split} comparison report.`,
        accent: "amber",
      },
      {
        label: "Top Uplift Segment",
        value: topSegment.segmentName,
        detail:
          topSegment.observedAte === null
            ? "No observed segment uplift was available from the live rollup response."
            : `Best live observed segment lift is ${formatEffectAsPercentagePoints(topSegment.observedAte)}.`,
        accent: "slate",
      },
      {
        label: "Budget Lead",
        value: topSegment.topBudgetSegment ? formatBudgetShare(topSegment.topBudgetSegment.budget_share) : "n/a",
        detail: topSegment.topBudgetSegment
          ? `Current Phase 5 recommendation lead is ${topSegment.topBudgetSegment.segment}.`
          : "No prioritized segment budget is available from the live closeout report.",
        accent: "coral",
      },
    ],
    systemState: {
      policyChampion: formatModelLabel(bundle.recommendations.policy_champion_model_name),
      policyValue: bundle.recommendations.policy_champion_value.toFixed(4),
      validationVerdict: bundle.segments.validation_verdict,
      testSplit: bundle.models.comparison_split,
      note: bundle.segments.validation_reason,
      stance: `Connected to ${bundle.health.service_name} ${bundle.health.api_version}. Current backend phase: ${bundle.health.current_phase}.`,
    },
    topSegments: prioritizedSegments.map((segment) => ({
      name: segment.segment,
      uplift: (segment.observed_conversion_ate ?? 0) * 100,
      budget: segment.budget_share * 100,
    })),
    suppressionWatch: suppressionCandidates.map((candidate) => ({
      name: candidate.group_value,
      signal: `${formatEffectAsPercentagePoints(candidate.observed_ate)} observed lift`,
      note: describeSuppressionSignal(candidate.group_column),
    })),
    recommendation: {
      summary: bundle.recommendations.final_action_summary,
      targetUsers: bundle.recommendations.top_target_user_count,
      suppressUsers: bundle.recommendations.top_suppress_user_count,
      source: `Live ${bundle.models.report_name} and Phase 5 closeout API responses`,
    },
    readiness: [
      {
        phase: "Dataset artifact",
        item: "Raw London campaign CSV is present for backend analysis.",
        status: bundle.health.readiness.dataset_ready ? "Ready" : "Missing",
        tone: bundle.health.readiness.dataset_ready ? "ready" : "missing",
      },
      {
        phase: "Prepared features",
        item: "Phase 2 processed splits and feature artifacts are available.",
        status: bundle.health.readiness.prepared_data_ready ? "Ready" : "Missing",
        tone: bundle.health.readiness.prepared_data_ready ? "ready" : "missing",
      },
      {
        phase: "Decision artifact",
        item: "Phase 5 closeout report is ready for policy and budget recommendations.",
        status: bundle.health.readiness.phase5_closeout_ready ? "Ready" : "Missing",
        tone: bundle.health.readiness.phase5_closeout_ready ? "ready" : "missing",
      },
      {
        phase: "API status",
        item: `Backend responded at ${bundle.health.timestamp_utc}.`,
        status: bundle.health.status === "ok" ? "Live" : bundle.health.status,
        tone: bundle.health.status === "ok" ? "live" : "missing",
      },
    ],
    nextUp: [
      "Replace the uplift insights snapshot with live Phase 4 segment and decile responses.",
      "Replace the recommendations snapshot with the live Phase 5 closeout response.",
      "Replace the dataset and model panel snapshot with live dataset and model registry data.",
    ],
  };
}

function getStatusBadgeClasses(mode: OverviewSourceMode) {
  if (mode === "live") {
    return "border border-emerald-700/15 bg-emerald-500/10 text-emerald-900";
  }

  if (mode === "connecting") {
    return "border border-amber-700/15 bg-amber-500/10 text-amber-900";
  }

  return "border border-rose-700/15 bg-rose-500/10 text-rose-900";
}

function getReadinessToneClasses(tone: OverviewReadinessItem["tone"]) {
  if (tone === "ready") {
    return "border-emerald-700/15 bg-emerald-500/10 text-emerald-900";
  }

  if (tone === "live") {
    return "border-teal-700/15 bg-teal-500/10 text-teal-900";
  }

  return "border-rose-700/15 bg-rose-500/10 text-rose-900";
}

export function OverviewLiveDashboard() {
  const [state, setState] = useState<OverviewState>(() => ({
    mode: "connecting",
    data: createFallbackViewModel("connecting", null),
    error: null,
  }));

  useEffect(() => {
    let isMounted = true;

    async function loadOverview() {
      try {
        const bundle = await fetchOverviewBundle();

        if (!isMounted) {
          return;
        }

        setState({
          mode: "live",
          data: createLiveViewModel(bundle),
          error: null,
        });
      } catch (error) {
        if (!isMounted) {
          return;
        }

        const message = error instanceof Error ? error.message : "Unknown API connection failure.";
        setState({
          mode: "fallback",
          data: createFallbackViewModel("fallback", message),
          error: message,
        });
      }
    }

    void loadOverview();

    return () => {
      isMounted = false;
    };
  }, []);

  const { headline, statusBadge, kpis, systemState, topSegments, suppressionWatch, recommendation, readiness, nextUp } =
    state.data;

  return (
    <main className="relative overflow-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-4 py-5 sm:px-6 lg:px-10">
        <AppHeader current="overview" sliceLabel="Phase 8 live overview integration" />

        <section className="mt-5 grid gap-5 lg:grid-cols-[1.45fr_0.85fr]">
          <SectionCard eyebrow={headline.label} title={headline.title} className="relative overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-36 bg-[radial-gradient(circle_at_top_left,_rgba(20,184,166,0.18),_transparent_58%),radial-gradient(circle_at_top_right,_rgba(251,146,60,0.16),_transparent_46%)]" />
            <div className="relative">
              <p className="max-w-2xl text-base leading-7 text-slate-600">{headline.description}</p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/uplift-insights"
                  className="rounded-full bg-slate-950 px-5 py-3 text-xs font-semibold uppercase tracking-[0.24em] text-white transition-transform hover:-translate-y-0.5"
                >
                  Open uplift insights
                </Link>
                <span
                  className={`rounded-full px-4 py-3 text-xs font-semibold uppercase tracking-[0.24em] ${getStatusBadgeClasses(statusBadge.tone)}`}
                >
                  {statusBadge.label}
                </span>
              </div>
              {state.error ? (
                <div className="mt-5 rounded-[24px] border border-rose-200 bg-rose-50 px-4 py-4 text-sm leading-6 text-rose-900">
                  <p className="font-semibold text-rose-950">Live overview is in fallback mode.</p>
                  <p className="mt-2">{state.error}</p>
                </div>
              ) : null}
              <div className="mt-8 grid gap-4 sm:grid-cols-2">
                {kpis.map((metric) => (
                  <MetricCard key={metric.label} {...metric} />
                ))}
              </div>
            </div>
          </SectionCard>

          <SectionCard eyebrow="Decision State" title="Operational readout">
            <div className="space-y-5">
              <div className="rounded-[26px] bg-slate-950 px-5 py-5 text-white">
                <p className="text-xs uppercase tracking-[0.28em] text-white/55">Policy champion</p>
                <div className="mt-3 flex items-end justify-between gap-4">
                  <div>
                    <p className="text-3xl font-semibold tracking-tight">{systemState.policyChampion}</p>
                    <p className="mt-2 text-sm text-white/65">Holdout value {systemState.policyValue}</p>
                  </div>
                  <div className="rounded-full bg-white/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-white/80">
                    {systemState.testSplit}
                  </div>
                </div>
              </div>

              <div className="rounded-[26px] border border-amber-200 bg-amber-50 px-5 py-5">
                <p className="text-xs uppercase tracking-[0.28em] text-amber-800">Validation verdict</p>
                <p className="mt-3 text-2xl font-semibold tracking-tight text-amber-950">
                  {systemState.validationVerdict}
                </p>
                <p className="mt-3 text-sm leading-6 text-amber-900/80">{systemState.note}</p>
              </div>

              <div className="rounded-[26px] border border-slate-200 bg-slate-50 px-5 py-5">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Frontend stance</p>
                <p className="mt-3 text-sm leading-6 text-slate-700">{systemState.stance}</p>
              </div>
            </div>
          </SectionCard>
        </section>

        <section className="mt-5 grid gap-5 xl:grid-cols-[1.15fr_0.85fr_0.9fr]">
          <SectionCard eyebrow="Uplift Pulse" title="Who is responding best?">
            <div className="space-y-4">
              {topSegments.map((segment, index) => (
                <div
                  key={segment.name}
                  className="rounded-[24px] border border-slate-900/8 bg-slate-50/90 px-4 py-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">
                        {index + 1}. {segment.name}
                      </p>
                      <p className="mt-1 text-xs uppercase tracking-[0.22em] text-slate-500">
                        Observed uplift
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-slate-950">
                        {formatPercentagePoint(segment.uplift)}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">Budget {segment.budget.toFixed(1)}%</p>
                    </div>
                  </div>
                  <div className="mt-4 h-2 rounded-full bg-slate-200">
                    <div
                      className="h-2 rounded-full bg-[linear-gradient(90deg,#0f766e,#14b8a6)]"
                      style={{ width: formatBarWidth(segment.uplift) }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Suppression Watch" title="Where response turns weak">
            <div className="space-y-4">
              {suppressionWatch.map((item) => (
                <div
                  key={item.name}
                  className="rounded-[24px] border border-rose-200/80 bg-rose-50 px-4 py-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <p className="text-sm font-semibold text-rose-950">{item.name}</p>
                    <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-rose-700">
                      Watch
                    </span>
                  </div>
                  <p className="mt-3 text-sm font-medium text-rose-900">{item.signal}</p>
                  <p className="mt-2 text-sm leading-6 text-rose-900/75">{item.note}</p>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Action Summary" title="What the system would do next">
            <div className="rounded-[26px] bg-[linear-gradient(180deg,#0f172a,#172554)] px-5 py-5 text-white">
              <p className="text-sm leading-7 text-white/85">{recommendation.summary}</p>
              <div className="mt-6 grid grid-cols-2 gap-3">
                <div className="rounded-[22px] bg-white/8 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-white/60">Target users</p>
                  <p className="mt-2 text-2xl font-semibold">{recommendation.targetUsers}</p>
                </div>
                <div className="rounded-[22px] bg-white/8 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-white/60">Suppress users</p>
                  <p className="mt-2 text-2xl font-semibold">{recommendation.suppressUsers}</p>
                </div>
              </div>
              <p className="mt-5 text-xs uppercase tracking-[0.22em] text-white/55">
                Source: {recommendation.source}
              </p>
            </div>
          </SectionCard>
        </section>

        <section className="mt-5 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <SectionCard eyebrow="Readiness" title="What is already live?">
            <div className="space-y-3">
              {readiness.map((item) => (
                <div
                  key={item.phase}
                  className="flex flex-col gap-2 rounded-[24px] border border-slate-900/8 bg-white/60 px-4 py-4 md:flex-row md:items-center md:justify-between"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-950">{item.phase}</p>
                    <p className="mt-1 text-sm text-slate-600">{item.item}</p>
                  </div>
                  <span
                    className={`inline-flex rounded-full border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.22em] ${getReadinessToneClasses(item.tone)}`}
                  >
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Next Up" title="What this live shell prepares for">
            <ul className="space-y-3">
              {nextUp.map((item) => (
                <li
                  key={item}
                  className="rounded-[22px] border border-slate-900/8 bg-slate-50/80 px-4 py-4 text-sm leading-6 text-slate-700"
                >
                  {item}
                </li>
              ))}
            </ul>
          </SectionCard>
        </section>
      </div>
    </main>
  );
}
