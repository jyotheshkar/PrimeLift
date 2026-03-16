"use client";

import { useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { SectionCard } from "@/components/section-card";
import { fetchUpliftInsightsData } from "@/lib/primelift-api";
import { upliftInsightsSnapshot } from "@/lib/uplift-insights-data";

type SourceMode = "connecting" | "live" | "fallback";

type SegmentAction = "prioritize" | "watch" | "suppress";

type DecileItem = {
  rank: number;
  uplift: number;
  tone: "positive" | "negative";
};

type SegmentRow = {
  segment: string;
  meanPredictedEffect: number;
  observedAte: number;
  positiveEffectShare: number;
  action: SegmentAction;
};

type CohortRow = {
  label: string;
  context: string;
  predicted: number;
  observed: number;
};

type ViewModel = {
  header: {
    eyebrow: string;
    title: string;
    description: string;
  };
  statusBadge: {
    label: string;
    tone: SourceMode;
  };
  modelState: {
    modelName: string;
    validationVerdict: string;
    overallObservedAte: number;
    topDecileGain: number;
    upliftConcentrationRatio: number;
    monotonicityBreakCount: number;
  };
  deciles: DecileItem[];
  segmentTable: SegmentRow[];
  topResponders: CohortRow[];
  suppressionWatch: CohortRow[];
  notes: string[];
  error: string | null;
};

function formatWidth(value: number, max = 4.5) {
  return `${Math.max(12, Math.min((Math.abs(value) / max) * 100, 100))}%`;
}

function toneClasses(tone: "positive" | "negative") {
  return tone === "positive"
    ? "border-teal-200 bg-teal-50 text-teal-950"
    : "border-rose-200 bg-rose-50 text-rose-950";
}

function actionClasses(action: SegmentAction) {
  if (action === "prioritize") {
    return "bg-teal-500/12 text-teal-900 border-teal-700/10";
  }
  if (action === "suppress") {
    return "bg-rose-500/12 text-rose-900 border-rose-700/10";
  }
  return "bg-amber-500/12 text-amber-900 border-amber-700/10";
}

function getStatusBadgeClasses(mode: SourceMode) {
  if (mode === "live") {
    return "border border-emerald-700/15 bg-emerald-500/10 text-emerald-900";
  }

  if (mode === "connecting") {
    return "border border-amber-700/15 bg-amber-500/10 text-amber-900";
  }

  return "border border-rose-700/15 bg-rose-500/10 text-rose-900";
}

function formatModelName(modelName: string) {
  const labelMap: Record<string, string> = {
    drlearner_conversion: "DRLearner conversion",
    xlearner_conversion: "XLearner conversion",
    causal_forest_conversion: "CausalForestDML conversion",
  };

  return labelMap[modelName] ?? modelName;
}

function toPercentagePoints(value: number | null | undefined) {
  return (value ?? 0) * 100;
}

function createFallbackViewModel(mode: SourceMode, error: string | null): ViewModel {
  return {
    header: {
      eyebrow: upliftInsightsSnapshot.header.eyebrow,
      title: upliftInsightsSnapshot.header.title,
      description:
        mode === "connecting"
          ? "Connecting this screen to the live Phase 4 backend outputs. Until the API responds, the saved uplift snapshot stays visible."
          : "The live Phase 4 API could not be reached, so this screen is using the saved uplift snapshot instead of live data.",
    },
    statusBadge: {
      label: mode === "connecting" ? "Connecting API" : "Snapshot fallback",
      tone: mode,
    },
    modelState: { ...upliftInsightsSnapshot.modelState },
    deciles: [...upliftInsightsSnapshot.deciles],
    segmentTable: [...upliftInsightsSnapshot.segmentTable],
    topResponders: [...upliftInsightsSnapshot.topResponders],
    suppressionWatch: [...upliftInsightsSnapshot.suppressionWatch],
    notes:
      error === null
        ? [...upliftInsightsSnapshot.notes]
        : [
            `Snapshot mode is active because the uplift API request failed: ${error}`,
            ...upliftInsightsSnapshot.notes.slice(0, 2),
          ],
    error,
  };
}

function createLiveViewModel(
  response: Awaited<ReturnType<typeof fetchUpliftInsightsData>>,
): ViewModel {
  const segmentReport = response.reports.find((report) => report.group_column === "segment");
  const segmentSummary = response.dimension_summaries.find(
    (summary) => summary.group_column === "segment",
  );
  const prioritizeSet = new Set(segmentSummary?.top_positive_groups ?? []);

  const segmentTable: SegmentRow[] = (segmentReport?.results ?? []).map((item) => {
    const segmentName = item.group_value;
    const action: SegmentAction =
      item.recommendation_label === "suppress"
        ? "suppress"
        : prioritizeSet.has(segmentName)
          ? "prioritize"
          : "watch";

    return {
      segment: segmentName,
      meanPredictedEffect: toPercentagePoints(item.mean_predicted_effect),
      observedAte: toPercentagePoints(item.observed_ate),
      positiveEffectShare: (item.positive_effect_share ?? 0) * 100,
      action,
    };
  });

  const deciles: DecileItem[] = response.deciles.map((item) => ({
    rank: item.decile_rank,
    uplift: toPercentagePoints(item.observed_ate),
    tone: (item.observed_ate ?? 0) > 0 ? "positive" : "negative",
  }));

  return {
    header: {
      eyebrow: "Phase 8 live uplift analysis",
      title: `${formatModelName(response.model_name)} is now driving this uplift screen from live Phase 4 artifacts.`,
      description:
        "This route now reads the live Phase 4 segment, cohort, and decile outputs from the backend. The ranking quality, responder pockets, and suppression zones below are no longer hard-coded.",
    },
    statusBadge: {
      label: "Live API connected",
      tone: "live",
    },
    modelState: {
      modelName: formatModelName(response.model_name),
      validationVerdict: response.validation_verdict,
      overallObservedAte: toPercentagePoints(response.overall_observed_ate),
      topDecileGain: toPercentagePoints(response.top_decile_gain_over_overall_ate),
      upliftConcentrationRatio: response.uplift_concentration_ratio ?? 0,
      monotonicityBreakCount: response.monotonicity_break_count,
    },
    deciles,
    segmentTable,
    topResponders: response.top_persuadable_cohorts.slice(0, 3).map((item) => ({
      label: item.group_value,
      context: item.group_column.replaceAll("_", " "),
      predicted: toPercentagePoints(Number(item.mean_predicted_effect)),
      observed: toPercentagePoints(Number(item.observed_ate)),
    })),
    suppressionWatch: response.suppression_candidates.slice(0, 3).map((item) => ({
      label: item.group_value,
      context: item.group_column.replaceAll("_", " "),
      predicted: toPercentagePoints(Number(item.mean_predicted_effect)),
      observed: toPercentagePoints(Number(item.observed_ate)),
    })),
    notes: [
      `Top persuadable deciles: ${response.top_persuadable_deciles.join(", ")}. Suppression candidate deciles: ${response.suppression_candidate_deciles.join(", ")}.`,
      `${response.positive_decile_count} positive deciles and ${response.negative_decile_count} negative deciles are visible in the holdout ranking.`,
      response.validation_reason,
    ],
    error: null,
  };
}

export function UpliftInsightsLiveDashboard() {
  const [viewModel, setViewModel] = useState<ViewModel>(() =>
    createFallbackViewModel("connecting", null),
  );

  useEffect(() => {
    let isMounted = true;

    async function load() {
      try {
        const response = await fetchUpliftInsightsData();

        if (!isMounted) {
          return;
        }

        setViewModel(createLiveViewModel(response));
      } catch (error) {
        if (!isMounted) {
          return;
        }

        const message = error instanceof Error ? error.message : "Unknown API connection failure.";
        setViewModel(createFallbackViewModel("fallback", message));
      }
    }

    void load();

    return () => {
      isMounted = false;
    };
  }, []);

  const { header, statusBadge, modelState, deciles, segmentTable, topResponders, suppressionWatch, notes, error } =
    viewModel;

  return (
    <main className="relative overflow-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-4 py-5 sm:px-6 lg:px-10">
        <AppHeader current="uplift" sliceLabel="Phase 8 live uplift insights integration" />

        <section className="mt-5 grid gap-5 lg:grid-cols-[1.35fr_0.95fr]">
          <SectionCard eyebrow={header.eyebrow} title={header.title} className="relative overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-32 bg-[radial-gradient(circle_at_top_left,_rgba(20,184,166,0.16),_transparent_56%),radial-gradient(circle_at_top_right,_rgba(59,130,246,0.12),_transparent_42%)]" />
            <div className="relative">
              <p className="max-w-3xl text-base leading-7 text-slate-600">{header.description}</p>

              <div className="mt-6 flex flex-wrap gap-3">
                <span
                  className={`rounded-full px-4 py-3 text-xs font-semibold uppercase tracking-[0.24em] ${getStatusBadgeClasses(statusBadge.tone)}`}
                >
                  {statusBadge.label}
                </span>
              </div>

              {error ? (
                <div className="mt-5 rounded-[24px] border border-rose-200 bg-rose-50 px-4 py-4 text-sm leading-6 text-rose-900">
                  <p className="font-semibold text-rose-950">Live uplift insights are in fallback mode.</p>
                  <p className="mt-2">{error}</p>
                </div>
              ) : null}

              <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-[26px] border border-slate-900/8 bg-white/70 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Model</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {modelState.modelName}
                  </p>
                </div>
                <div className="rounded-[26px] border border-slate-900/8 bg-white/70 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Baseline ATE</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    +{modelState.overallObservedAte.toFixed(2)}pp
                  </p>
                </div>
                <div className="rounded-[26px] border border-slate-900/8 bg-white/70 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Top decile gain</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    +{modelState.topDecileGain.toFixed(2)}pp
                  </p>
                </div>
                <div className="rounded-[26px] border border-slate-900/8 bg-white/70 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Concentration ratio</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {modelState.upliftConcentrationRatio.toFixed(2)}x
                  </p>
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard eyebrow="Reading the ranking" title="How trustworthy is this uplift order?">
            <div className="space-y-4">
              <div className="rounded-[26px] border border-amber-200 bg-amber-50 px-5 py-5">
                <p className="text-xs uppercase tracking-[0.24em] text-amber-800">Validation verdict</p>
                <p className="mt-3 text-2xl font-semibold tracking-tight text-amber-950">
                  {modelState.validationVerdict}
                </p>
              </div>
              <div className="rounded-[26px] bg-slate-950 px-5 py-5 text-white">
                <p className="text-xs uppercase tracking-[0.24em] text-white/55">Monotonicity breaks</p>
                <p className="mt-3 text-3xl font-semibold tracking-tight">
                  {modelState.monotonicityBreakCount}
                </p>
                <p className="mt-2 text-sm leading-6 text-white/68">
                  The score ordering is directionally useful, but it still bends in the middle ranks.
                </p>
              </div>
              <ul className="space-y-3">
                {notes.map((note) => (
                  <li
                    key={note}
                    className="rounded-[22px] border border-slate-900/8 bg-white/70 px-4 py-4 text-sm leading-6 text-slate-700"
                  >
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          </SectionCard>
        </section>

        <section className="mt-5 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          <SectionCard eyebrow="Uplift by segment" title="Observed response once the model groups users">
            <div className="space-y-4">
              {segmentTable.map((segment) => (
                <div
                  key={segment.segment}
                  className="rounded-[24px] border border-slate-900/8 bg-slate-50/90 px-4 py-4"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <p className="text-sm font-semibold text-slate-950">{segment.segment}</p>
                        <span
                          className={`rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] ${actionClasses(segment.action)}`}
                        >
                          {segment.action}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-slate-600">
                        Positive-score share {segment.positiveEffectShare.toFixed(2)}%
                      </p>
                    </div>

                    <div className="grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">
                          Mean predicted effect
                        </p>
                        <p className="mt-1 font-semibold text-slate-950">
                          +{segment.meanPredictedEffect.toFixed(2)}pp
                        </p>
                      </div>
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">
                          Observed ATE
                        </p>
                        <p
                          className={`mt-1 font-semibold ${
                            segment.observedAte >= 0 ? "text-teal-800" : "text-rose-800"
                          }`}
                        >
                          {segment.observedAte >= 0 ? "+" : ""}
                          {segment.observedAte.toFixed(2)}pp
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div>
                      <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-slate-500">
                        Predicted
                      </p>
                      <div className="h-2 rounded-full bg-slate-200">
                        <div
                          className="h-2 rounded-full bg-[linear-gradient(90deg,#0f766e,#14b8a6)]"
                          style={{ width: formatWidth(segment.meanPredictedEffect) }}
                        />
                      </div>
                    </div>
                    <div>
                      <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-slate-500">
                        Observed
                      </p>
                      <div className="h-2 rounded-full bg-slate-200">
                        <div
                          className={`h-2 rounded-full ${
                            segment.observedAte >= 0
                              ? "bg-[linear-gradient(90deg,#0f766e,#22c55e)]"
                              : "bg-[linear-gradient(90deg,#be123c,#fb7185)]"
                          }`}
                          style={{ width: formatWidth(segment.observedAte) }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Decile view" title="How the uplift signal behaves down-rank">
            <div className="grid gap-3 sm:grid-cols-2">
              {deciles.map((decile) => (
                <div
                  key={decile.rank}
                  className={`rounded-[24px] border px-4 py-4 ${toneClasses(decile.tone)}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] opacity-70">
                        Decile {decile.rank}
                      </p>
                      <p className="mt-3 text-2xl font-semibold tracking-tight">
                        {decile.uplift >= 0 ? "+" : ""}
                        {decile.uplift.toFixed(2)}pp
                      </p>
                    </div>
                    <span className="rounded-full bg-white/70 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em]">
                      {decile.tone}
                    </span>
                  </div>
                  <div className="mt-4 h-2 rounded-full bg-black/8">
                    <div
                      className={`h-2 rounded-full ${
                        decile.tone === "positive"
                          ? "bg-[linear-gradient(90deg,#0f766e,#14b8a6)]"
                          : "bg-[linear-gradient(90deg,#be123c,#fb7185)]"
                      }`}
                      style={{ width: formatWidth(decile.uplift) }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </section>

        <section className="mt-5 grid gap-5 xl:grid-cols-[1fr_1fr]">
          <SectionCard eyebrow="Positive responders" title="Cohorts the model wants more of">
            <div className="space-y-4">
              {topResponders.map((item) => (
                <div
                  key={item.label}
                  className="rounded-[24px] border border-teal-200 bg-teal-50 px-4 py-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-teal-950">{item.label}</p>
                      <p className="mt-1 text-[11px] uppercase tracking-[0.22em] text-teal-800/80">
                        {item.context}
                      </p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-teal-800">
                      Prioritize
                    </span>
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-teal-950 sm:grid-cols-2">
                    <p>Predicted +{item.predicted.toFixed(2)}pp</p>
                    <p>Observed +{item.observed.toFixed(2)}pp</p>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Negative responders" title="Cohorts that need restraint">
            <div className="space-y-4">
              {suppressionWatch.map((item) => (
                <div
                  key={item.label}
                  className="rounded-[24px] border border-rose-200 bg-rose-50 px-4 py-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-rose-950">{item.label}</p>
                      <p className="mt-1 text-[11px] uppercase tracking-[0.22em] text-rose-800/80">
                        {item.context}
                      </p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-rose-700">
                      Suppress
                    </span>
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-rose-950 sm:grid-cols-2">
                    <p>Predicted +{item.predicted.toFixed(2)}pp</p>
                    <p>
                      {item.observed >= 0 ? "+" : ""}
                      {item.observed.toFixed(2)}pp observed
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </section>
      </div>
    </main>
  );
}
