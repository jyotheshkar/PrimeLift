"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { SectionCard } from "@/components/section-card";
import {
  fetchRecommendationsData,
  type AnalysisRecommendationsResponse,
} from "@/lib/primelift-api";
import { recommendationsSnapshot } from "@/lib/recommendations-data";

type SourceMode = "connecting" | "live" | "fallback";

type BudgetItem = {
  segment: string;
  budgetShare: number;
  budgetAmount: number;
  conversionEffect: number;
  revenueEffect: number;
  policyAlignment: string;
};

type SuppressionItem = {
  segment: string;
  observedAte: number;
  revenueEffect: number;
  budgetAmount: number;
  policyAlignment: string;
};

type UserItem = {
  userId: string;
  segment: string;
  borough: string;
  predictedEffect: number;
};

type ViewModel = {
  statusBadge: { label: string; tone: SourceMode };
  header: { eyebrow: string; title: string; description: string };
  champion: {
    modelName: string;
    value: number;
    gainOverRunnerUp: number;
    gainOverAlwaysControl: number;
    reason: string;
  };
  finalSummary: string;
  budgetPlan: BudgetItem[];
  suppressedSegments: SuppressionItem[];
  targetUsers: UserItem[];
  suppressUsers: UserItem[];
  notes: string[];
  error: string | null;
};

type State = { mode: SourceMode; data: ViewModel };

const MODEL_LABELS: Record<string, string> = {
  drlearner_conversion: "DRLearner",
  xlearner_conversion: "XLearner",
  causal_forest_conversion: "CausalForestDML",
  drlearner_revenue: "DRLearner Revenue",
  drpolicytree_conversion: "DRPolicyTree",
  drpolicyforest_conversion: "DRPolicyForest",
};

function formatModelLabel(name: string) {
  return MODEL_LABELS[name] ?? name;
}

function createFallbackViewModel(mode: SourceMode, error: string | null): ViewModel {
  const snap = recommendationsSnapshot;
  return {
    statusBadge: {
      label: mode === "connecting" ? "Connecting API" : "Snapshot fallback",
      tone: mode,
    },
    header: {
      eyebrow: snap.header.eyebrow,
      title: snap.header.title,
      description:
        mode === "connecting"
          ? "Connecting to the local FastAPI backend. Until it responds, this screen uses the saved Phase 5 artifact snapshot."
          : "The live backend could not be reached, so this screen is using the saved Phase 5 artifact snapshot.",
    },
    champion: { ...snap.champion },
    finalSummary: snap.finalSummary,
    budgetPlan: snap.budgetPlan.map((item) => ({ ...item })),
    suppressedSegments: snap.suppressedSegments.map((item) => ({ ...item })),
    targetUsers: snap.targetUsers.map((user) => ({ ...user })),
    suppressUsers: snap.suppressUsers.map((user) => ({ ...user })),
    notes: [...snap.notes],
    error,
  };
}

function createLiveViewModel(response: AnalysisRecommendationsResponse): ViewModel {
  const snap = recommendationsSnapshot;

  const budgetPlan: BudgetItem[] = response.report.prioritized_segments.map((seg) => {
    const snapItem = snap.budgetPlan.find((s) => s.segment === seg.segment);
    return {
      segment: seg.segment,
      budgetShare: seg.budget_share * 100,
      budgetAmount: snapItem?.budgetAmount ?? seg.budget_share * 100_000,
      conversionEffect:
        seg.observed_conversion_ate !== null
          ? seg.observed_conversion_ate * 100
          : (snapItem?.conversionEffect ?? 0),
      revenueEffect: snapItem?.revenueEffect ?? 0,
      policyAlignment: snapItem?.policyAlignment ?? "champion_policy_treat",
    };
  });

  const suppressedSegments: SuppressionItem[] = response.report.suppressed_segments.map((seg) => {
    const snapItem = snap.suppressedSegments.find((s) => s.segment === seg.segment);
    return {
      segment: seg.segment,
      observedAte:
        seg.observed_conversion_ate !== null
          ? seg.observed_conversion_ate * 100
          : (snapItem?.observedAte ?? 0),
      revenueEffect: snapItem?.revenueEffect ?? 0,
      budgetAmount: 0,
      policyAlignment: "champion_policy_holdout",
    };
  });

  return {
    statusBadge: { label: "Live API connected", tone: "live" },
    header: {
      eyebrow: "Phase 5 ML decision engine — live",
      title:
        "PrimeLift is reading live policy and budget outputs from the Phase 5 closeout endpoint.",
      description:
        "The champion model, budget plan, and suppression segments below are sourced directly from the saved Phase 5 artifacts via the local FastAPI backend.",
    },
    champion: {
      modelName: formatModelLabel(response.policy_champion_model_name),
      value: response.policy_champion_value,
      gainOverRunnerUp: snap.champion.gainOverRunnerUp,
      gainOverAlwaysControl: snap.champion.gainOverAlwaysControl,
      reason: response.champion_is_ml_model
        ? `${formatModelLabel(response.policy_champion_model_name)} is the current champion because it beats all policy baselines on the holdout split.`
        : snap.champion.reason,
    },
    finalSummary: response.final_action_summary,
    budgetPlan,
    suppressedSegments,
    targetUsers: snap.targetUsers.map((user) => ({ ...user })),
    suppressUsers: snap.suppressUsers.map((user) => ({ ...user })),
    notes: [
      response.champion_is_ml_model
        ? "The policy champion is ML-driven rather than a naive always-treat baseline."
        : "The policy champion is a naive baseline.",
      `Budget is distributed across ${response.prioritized_segment_count} prioritised segment(s); ${response.suppressed_segment_count} segment(s) are suppressed.`,
      `The current policy targets ${response.top_target_user_count} users and suppresses ${response.top_suppress_user_count} users.`,
    ],
    error: null,
  };
}

function statusBadgeClasses(mode: SourceMode) {
  if (mode === "live") return "border border-emerald-700/15 bg-emerald-500/10 text-emerald-900";
  if (mode === "connecting") return "border border-amber-700/15 bg-amber-500/10 text-amber-900";
  return "border border-rose-700/15 bg-rose-500/10 text-rose-900";
}

function formatBudgetWidth(value: number) {
  return `${Math.max(14, Math.min(value, 100))}%`;
}

function alignmentTone(alignment: string) {
  if (alignment === "champion_policy_treat") {
    return "bg-teal-500/12 text-teal-900 border-teal-700/10";
  }
  if (alignment === "champion_policy_holdout") {
    return "bg-slate-900/8 text-slate-900 border-slate-900/10";
  }
  return "bg-amber-500/12 text-amber-900 border-amber-700/10";
}

export function RecommendationsLiveDashboard() {
  const [state, setState] = useState<State>(() => ({
    mode: "connecting",
    data: createFallbackViewModel("connecting", null),
  }));

  useEffect(() => {
    let isMounted = true;

    async function load() {
      try {
        const response = await fetchRecommendationsData();
        if (!isMounted) return;
        setState({ mode: "live", data: createLiveViewModel(response) });
      } catch (error) {
        if (!isMounted) return;
        const message = error instanceof Error ? error.message : "Unknown API connection failure.";
        setState({ mode: "fallback", data: createFallbackViewModel("fallback", message) });
      }
    }

    void load();
    return () => {
      isMounted = false;
    };
  }, []);

  const { statusBadge, header, champion, finalSummary, budgetPlan, suppressedSegments, targetUsers, suppressUsers, notes, error } =
    state.data;

  return (
    <main className="relative overflow-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-4 py-5 sm:px-6 lg:px-10">
        <AppHeader current="recommendations" sliceLabel="Phase 8 live recommendations integration" />

        <section className="mt-5 grid gap-5 lg:grid-cols-[1.35fr_0.95fr]">
          <SectionCard eyebrow={header.eyebrow} title={header.title} className="relative overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-32 bg-[radial-gradient(circle_at_top_left,_rgba(15,23,42,0.12),_transparent_52%),radial-gradient(circle_at_top_right,_rgba(20,184,166,0.16),_transparent_48%)]" />
            <div className="relative">
              <p className="max-w-3xl text-base leading-7 text-slate-600">{header.description}</p>

              <div className="mt-6 flex flex-wrap gap-3">
                <span className={`rounded-full px-4 py-3 text-xs font-semibold uppercase tracking-[0.24em] ${statusBadgeClasses(statusBadge.tone)}`}>
                  {statusBadge.label}
                </span>
              </div>

              {error ? (
                <div className="mt-5 rounded-[24px] border border-rose-200 bg-rose-50 px-4 py-4 text-sm leading-6 text-rose-900">
                  <p className="font-semibold text-rose-950">Recommendations are in fallback mode.</p>
                  <p className="mt-2">{error}</p>
                </div>
              ) : null}

              <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-[26px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Policy champion</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {champion.modelName}
                  </p>
                </div>
                <div className="rounded-[26px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Holdout value</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {champion.value.toFixed(4)}
                  </p>
                </div>
                <div className="rounded-[26px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Gain vs runner-up</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    +{champion.gainOverRunnerUp.toFixed(4)}
                  </p>
                </div>
                <div className="rounded-[26px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Gain vs control</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    +{champion.gainOverAlwaysControl.toFixed(4)}
                  </p>
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard eyebrow="Final stance" title="Current operating instruction">
            <div className="space-y-4">
              <div className="rounded-[26px] bg-[linear-gradient(180deg,#0f172a,#172554)] px-5 py-5 text-white">
                <p className="text-sm leading-7 text-white/88">{finalSummary}</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Link
                  href="/dataset-models"
                  className="rounded-full bg-slate-950 px-5 py-3 text-xs font-semibold uppercase tracking-[0.24em] text-white transition-transform hover:-translate-y-0.5"
                >
                  Open dataset panel
                </Link>
              </div>
              <div className="rounded-[26px] border border-emerald-200 bg-emerald-50 px-5 py-5">
                <p className="text-xs uppercase tracking-[0.24em] text-emerald-800">Champion reason</p>
                <p className="mt-3 text-sm leading-6 text-emerald-950">{champion.reason}</p>
              </div>
              <ul className="space-y-3">
                {notes.map((note) => (
                  <li
                    key={note}
                    className="rounded-[22px] border border-slate-900/8 bg-white/72 px-4 py-4 text-sm leading-6 text-slate-700"
                  >
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          </SectionCard>
        </section>

        <section className="mt-5 grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
          <SectionCard eyebrow="Budget allocation" title="Where the model wants spend to go">
            <div className="space-y-4">
              {budgetPlan.map((item) => (
                <div
                  key={item.segment}
                  className="rounded-[24px] border border-slate-900/8 bg-slate-50/90 px-4 py-4"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <p className="text-sm font-semibold text-slate-950">{item.segment}</p>
                        <span
                          className={`rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] ${alignmentTone(item.policyAlignment)}`}
                        >
                          {item.policyAlignment.replaceAll("_", " ")}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-slate-600">
                        Budget £{item.budgetAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </p>
                    </div>

                    <div className="grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">
                          Conversion effect
                        </p>
                        <p className="mt-1 font-semibold text-slate-950">
                          +{item.conversionEffect.toFixed(2)}pp
                        </p>
                      </div>
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">
                          Revenue effect
                        </p>
                        <p className="mt-1 font-semibold text-slate-950">
                          +{item.revenueEffect.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4">
                    <div className="mb-2 flex items-center justify-between text-[11px] uppercase tracking-[0.2em] text-slate-500">
                      <span>Budget share</span>
                      <span>{item.budgetShare.toFixed(2)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-200">
                      <div
                        className="h-2 rounded-full bg-[linear-gradient(90deg,#0f172a,#14b8a6)]"
                        style={{ width: formatBudgetWidth(item.budgetShare) }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Suppression plan" title="Where the system deliberately holds back">
            <div className="space-y-4">
              {suppressedSegments.map((item) => (
                <div
                  key={item.segment}
                  className="rounded-[24px] border border-rose-200 bg-rose-50 px-4 py-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-rose-950">{item.segment}</p>
                      <p className="mt-1 text-[11px] uppercase tracking-[0.22em] text-rose-800/80">
                        {item.policyAlignment.replaceAll("_", " ")}
                      </p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-rose-700">
                      Zero budget
                    </span>
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-rose-950 sm:grid-cols-2">
                    <p>{item.observedAte >= 0 ? "+" : ""}{item.observedAte.toFixed(2)}pp observed</p>
                    <p>Revenue signal +{item.revenueEffect.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </section>

        <section className="mt-5 grid gap-5 xl:grid-cols-[1fr_1fr]">
          <SectionCard eyebrow="Top target users" title="Who rises to the top of the policy stack">
            <div className="space-y-4">
              {targetUsers.map((user) => (
                <div
                  key={user.userId}
                  className="rounded-[24px] border border-teal-200 bg-teal-50 px-4 py-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-teal-950">{user.userId}</p>
                      <p className="mt-1 text-sm text-teal-900/80">
                        {user.segment} · {user.borough}
                      </p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-teal-800">
                      Target
                    </span>
                  </div>
                  <p className="mt-4 text-sm font-medium text-teal-950">
                    Predicted effect +{user.predictedEffect.toFixed(2)}pp
                  </p>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Top suppress users" title="Who the model says to avoid">
            <div className="space-y-4">
              {suppressUsers.map((user) => (
                <div
                  key={user.userId}
                  className="rounded-[24px] border border-rose-200 bg-rose-50 px-4 py-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-rose-950">{user.userId}</p>
                      <p className="mt-1 text-sm text-rose-900/80">
                        {user.segment} · {user.borough}
                      </p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-rose-700">
                      Suppress
                    </span>
                  </div>
                  <p className="mt-4 text-sm font-medium text-rose-950">
                    Predicted effect {user.predictedEffect.toFixed(2)}pp
                  </p>
                </div>
              ))}
            </div>
          </SectionCard>
        </section>
      </div>
    </main>
  );
}
