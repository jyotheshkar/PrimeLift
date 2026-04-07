"use client";

import { useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { SectionCard } from "@/components/section-card";
import {
  fetchDatasetModelsBundle,
  postDatasetGenerate,
  type AnalysisModelsResponse,
  type DatasetSampleResponse,
} from "@/lib/primelift-api";
import { datasetModelsSnapshot } from "@/lib/dataset-models-data";

type SourceMode = "connecting" | "live" | "fallback";

type SampleRow = {
  userId: string;
  borough: string;
  segment: string;
  treatment: number | string;
  conversion: number | string;
  revenue: string;
};

type SplitSummary = { name: string; rows: string; rate: string };
type SchemaGroup = { label: string; count: number; columns: string[] };
type ModelEntry = { name: string; family: string; status: string; role: string };
type ModelSelection = {
  conversionChampion: string;
  conversionChallenger: string;
  revenueChampion: string;
  policyChampion: string;
};
type TrainingStatus = { label: string; status: string; detail: string };

type ViewModel = {
  statusBadge: { label: string; tone: SourceMode };
  header: { eyebrow: string; title: string; description: string };
  dataset: {
    rowCount: string;
    columnCount: number;
    rawFeatureCount: number;
    transformedFeatureCount: number;
    splitSummary: SplitSummary[];
    schemaGroups: SchemaGroup[];
    sampleRows: SampleRow[];
  };
  modelRegistry: ModelEntry[];
  modelSelection: ModelSelection;
  trainingStatus: TrainingStatus[];
  error: string | null;
};

type State = { mode: SourceMode; data: ViewModel; generating: boolean };

const MODEL_LABELS: Record<string, string> = {
  drlearner_conversion: "DRLearner conversion",
  xlearner_conversion: "XLearner conversion",
  causal_forest_conversion: "CausalForestDML conversion",
  drlearner_revenue: "DRLearner revenue",
  drpolicytree_conversion: "DRPolicyTree conversion",
  drpolicyforest_conversion: "DRPolicyForest",
};

function formatModelLabel(name: string) {
  return MODEL_LABELS[name] ?? name;
}

function extractSampleRow(record: Record<string, unknown>): SampleRow {
  return {
    userId: String(record["user_id"] ?? ""),
    borough: String(record["london_borough"] ?? ""),
    segment: String(record["segment"] ?? ""),
    treatment: Number(record["treatment"] ?? 0),
    conversion: Number(record["conversion"] ?? 0),
    revenue: Number(record["revenue"] ?? 0).toFixed(2),
  };
}

function createFallbackViewModel(mode: SourceMode, error: string | null): ViewModel {
  const snap = datasetModelsSnapshot;
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
          ? "Connecting to the local FastAPI backend. Until it responds, this screen uses the saved Phase 2–3 artifact snapshot."
          : "The live backend could not be reached, so this screen is using the saved Phase 2–3 artifact snapshot.",
    },
    dataset: {
      rowCount: snap.dataset.rowCount,
      columnCount: snap.dataset.columnCount,
      rawFeatureCount: snap.dataset.rawFeatureCount,
      transformedFeatureCount: snap.dataset.transformedFeatureCount,
      splitSummary: snap.dataset.splitSummary.map((s) => ({ ...s })),
      schemaGroups: snap.dataset.schemaGroups.map((g) => ({
        label: g.label,
        count: g.count,
        columns: [...g.columns],
      })),
      sampleRows: snap.dataset.sampleRows.map((r) => ({ ...r, treatment: r.treatment, conversion: r.conversion })),
    },
    modelRegistry: snap.modelRegistry.map((m) => ({ ...m })),
    modelSelection: { ...snap.modelSelection },
    trainingStatus: snap.trainingStatus.map((t) => ({ ...t })),
    error,
  };
}

function createLiveViewModel(
  sample: DatasetSampleResponse,
  models: AnalysisModelsResponse,
): ViewModel {
  const snap = datasetModelsSnapshot;

  const sampleRows = sample.records.slice(0, 10).map(extractSampleRow);

  const modelSelection: ModelSelection = {
    conversionChampion: formatModelLabel(models.conversion_champion_model_name),
    conversionChallenger: models.conversion_challenger_model_name
      ? formatModelLabel(models.conversion_challenger_model_name)
      : "None",
    revenueChampion: formatModelLabel(models.revenue_champion_model_name),
    policyChampion: snap.modelSelection.policyChampion,
  };

  return {
    statusBadge: { label: "Live API connected", tone: "live" },
    header: {
      eyebrow: "Phase 2 and Phase 3 asset view — live",
      title: "Live dataset sample and model registry are sourced from the local FastAPI backend.",
      description:
        "The sample preview below uses the live /dataset/sample endpoint. Model selection reflects the saved Phase 3 champion comparison report.",
    },
    dataset: {
      rowCount: sample.available_rows.toLocaleString(),
      columnCount: sample.columns.length,
      rawFeatureCount: snap.dataset.rawFeatureCount,
      transformedFeatureCount: snap.dataset.transformedFeatureCount,
      splitSummary: snap.dataset.splitSummary.map((s) => ({ ...s })),
      schemaGroups: snap.dataset.schemaGroups.map((g) => ({
        label: g.label,
        count: g.count,
        columns: [...g.columns],
      })),
      sampleRows,
    },
    modelRegistry: snap.modelRegistry.map((m) => ({ ...m })),
    modelSelection,
    trainingStatus: snap.trainingStatus.map((t) => {
      if (t.label === "Frontend integration") {
        return { label: t.label, status: "Complete", detail: "Live API wiring complete via Phase 8 integration." };
      }
      return { ...t };
    }),
    error: null,
  };
}

function statusBadgeClasses(mode: SourceMode) {
  if (mode === "live") return "border border-emerald-700/15 bg-emerald-500/10 text-emerald-900";
  if (mode === "connecting") return "border border-amber-700/15 bg-amber-500/10 text-amber-900";
  return "border border-rose-700/15 bg-rose-500/10 text-rose-900";
}

function statusTone(status: string) {
  if (status === "Complete" || status === "implemented") {
    return "bg-emerald-500/12 text-emerald-900 border-emerald-700/10";
  }
  return "bg-amber-500/12 text-amber-900 border-amber-700/10";
}

export function DatasetModelsLiveDashboard() {
  const [state, setState] = useState<State>(() => ({
    mode: "connecting",
    data: createFallbackViewModel("connecting", null),
    generating: false,
  }));

  async function loadData() {
    try {
      const { sample, models } = await fetchDatasetModelsBundle();
      setState((prev) => ({
        ...prev,
        mode: "live",
        data: createLiveViewModel(sample, models),
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown API connection failure.";
      setState((prev) => ({
        ...prev,
        mode: "fallback",
        data: createFallbackViewModel("fallback", message),
      }));
    }
  }

  useEffect(() => {
    let isMounted = true;

    async function load() {
      try {
        const { sample, models } = await fetchDatasetModelsBundle();
        if (!isMounted) return;
        setState((prev) => ({
          ...prev,
          mode: "live",
          data: createLiveViewModel(sample, models),
        }));
      } catch (error) {
        if (!isMounted) return;
        const message = error instanceof Error ? error.message : "Unknown API connection failure.";
        setState((prev) => ({
          ...prev,
          mode: "fallback",
          data: createFallbackViewModel("fallback", message),
        }));
      }
    }

    void load();
    return () => {
      isMounted = false;
    };
  }, []);

  async function handleGenerate() {
    setState((prev) => ({ ...prev, generating: true }));
    try {
      await postDatasetGenerate();
      await loadData();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Generation failed.";
      setState((prev) => ({
        ...prev,
        generating: false,
        data: { ...prev.data, error: message },
      }));
      return;
    }
    setState((prev) => ({ ...prev, generating: false }));
  }

  const { statusBadge, header, dataset, modelRegistry, modelSelection, trainingStatus, error } =
    state.data;

  return (
    <main className="relative overflow-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-4 py-5 sm:px-6 lg:px-10">
        <AppHeader current="dataset-models" sliceLabel="Phase 8 live dataset and model integration" />

        <section className="mt-5 grid gap-5 lg:grid-cols-[1.3fr_1fr]">
          <SectionCard eyebrow={header.eyebrow} title={header.title} className="relative overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-32 bg-[radial-gradient(circle_at_top_left,_rgba(20,184,166,0.14),_transparent_54%),radial-gradient(circle_at_top_right,_rgba(99,102,241,0.14),_transparent_44%)]" />
            <div className="relative">
              <p className="max-w-3xl text-base leading-7 text-slate-600">{header.description}</p>

              <div className="mt-6 flex flex-wrap gap-3">
                <span className={`rounded-full px-4 py-3 text-xs font-semibold uppercase tracking-[0.24em] ${statusBadgeClasses(statusBadge.tone)}`}>
                  {statusBadge.label}
                </span>
              </div>

              {error ? (
                <div className="mt-5 rounded-[24px] border border-rose-200 bg-rose-50 px-4 py-4 text-sm leading-6 text-rose-900">
                  <p className="font-semibold text-rose-950">Dataset panel is in fallback mode.</p>
                  <p className="mt-2">{error}</p>
                </div>
              ) : null}

              <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-[26px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Dataset rows</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {dataset.rowCount}
                  </p>
                </div>
                <div className="rounded-[26px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Columns</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {dataset.columnCount}
                  </p>
                </div>
                <div className="rounded-[26px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Raw features</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {dataset.rawFeatureCount}
                  </p>
                </div>
                <div className="rounded-[26px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Transformed features</p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {dataset.transformedFeatureCount}
                  </p>
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard eyebrow="Dataset actions" title="Generate or refresh the London campaign dataset">
            <div className="space-y-4">
              <div className="rounded-[26px] bg-slate-950 px-5 py-5 text-white">
                <p className="text-xs uppercase tracking-[0.24em] text-white/55">Generation flow</p>
                <p className="mt-3 text-sm leading-7 text-white/85">
                  Trigger the backend to regenerate the 100k-row London campaign dataset from scratch using the fixed synthetic seed. The sample preview will refresh automatically.
                </p>
                <div className="mt-5 flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => void handleGenerate()}
                    disabled={state.generating}
                    className="rounded-full bg-white px-5 py-3 text-xs font-semibold uppercase tracking-[0.24em] text-slate-950 disabled:opacity-50"
                  >
                    {state.generating ? "Generating…" : "Generate dataset"}
                  </button>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {dataset.splitSummary.map((split) => (
                  <div
                    key={split.name}
                    className="rounded-[22px] border border-slate-900/8 bg-white/72 px-4 py-4"
                  >
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{split.name}</p>
                    <p className="mt-3 text-xl font-semibold tracking-tight text-slate-950">{split.rows}</p>
                    <p className="mt-2 text-sm text-slate-600">{split.rate}</p>
                  </div>
                ))}
              </div>
            </div>
          </SectionCard>
        </section>

        <section className="mt-5 grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
          <SectionCard eyebrow="Schema summary" title="How the dataset is organized for modeling">
            <div className="space-y-4">
              {dataset.schemaGroups.map((group) => (
                <div
                  key={group.label}
                  className="rounded-[24px] border border-slate-900/8 bg-slate-50/90 px-4 py-4"
                >
                  <div className="flex items-center justify-between gap-4">
                    <p className="text-sm font-semibold text-slate-950">{group.label}</p>
                    <span className="rounded-full border border-slate-900/10 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-700">
                      {group.count}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {group.columns.map((column) => (
                      <span
                        key={column}
                        className="rounded-full border border-slate-900/8 bg-white px-3 py-2 text-xs font-medium text-slate-700"
                      >
                        {column}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Sample data preview" title="What the saved London experiment rows look like">
            <div className="overflow-hidden rounded-[26px] border border-slate-900/8 bg-white/82">
              <div className="grid grid-cols-[1.2fr_1fr_1.1fr_0.6fr_0.7fr_0.8fr] gap-3 border-b border-slate-900/8 px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                <span>User</span>
                <span>Borough</span>
                <span>Segment</span>
                <span>T</span>
                <span>Conv</span>
                <span>Revenue</span>
              </div>
              {dataset.sampleRows.map((row) => (
                <div
                  key={row.userId}
                  className="grid grid-cols-[1.2fr_1fr_1.1fr_0.6fr_0.7fr_0.8fr] gap-3 border-b border-slate-900/6 px-4 py-4 text-sm text-slate-700 last:border-b-0"
                >
                  <span className="font-semibold text-slate-950">{row.userId}</span>
                  <span>{row.borough}</span>
                  <span>{row.segment}</span>
                  <span>{row.treatment}</span>
                  <span>{row.conversion}</span>
                  <span>{row.revenue}</span>
                </div>
              ))}
            </div>
          </SectionCard>
        </section>

        <section className="mt-5 grid gap-5 xl:grid-cols-[1fr_1fr]">
          <SectionCard eyebrow="Model registry" title="Which estimators are already in the stack">
            <div className="space-y-4">
              {modelRegistry.map((model) => (
                <div
                  key={model.name}
                  className="rounded-[24px] border border-slate-900/8 bg-slate-50/90 px-4 py-4"
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-950">{model.name}</p>
                      <p className="mt-1 text-sm text-slate-600">
                        {model.family} · {model.role}
                      </p>
                    </div>
                    <span
                      className={`rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] ${statusTone(model.status)}`}
                    >
                      {model.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Training and scoring status" title="What the saved artifacts already confirm">
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-[22px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Conversion champion</p>
                  <p className="mt-3 text-xl font-semibold tracking-tight text-slate-950">
                    {modelSelection.conversionChampion}
                  </p>
                </div>
                <div className="rounded-[22px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Challenger</p>
                  <p className="mt-3 text-xl font-semibold tracking-tight text-slate-950">
                    {modelSelection.conversionChallenger}
                  </p>
                </div>
                <div className="rounded-[22px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Revenue champion</p>
                  <p className="mt-3 text-xl font-semibold tracking-tight text-slate-950">
                    {modelSelection.revenueChampion}
                  </p>
                </div>
                <div className="rounded-[22px] border border-slate-900/8 bg-white/72 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Policy champion</p>
                  <p className="mt-3 text-xl font-semibold tracking-tight text-slate-950">
                    {modelSelection.policyChampion}
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                {trainingStatus.map((item) => (
                  <div
                    key={item.label}
                    className="flex flex-col gap-2 rounded-[24px] border border-slate-900/8 bg-slate-50/90 px-4 py-4 md:flex-row md:items-center md:justify-between"
                  >
                    <div>
                      <p className="text-sm font-semibold text-slate-950">{item.label}</p>
                      <p className="mt-1 text-sm text-slate-600">{item.detail}</p>
                    </div>
                    <span
                      className={`inline-flex rounded-full border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.22em] ${statusTone(item.status)}`}
                    >
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </SectionCard>
        </section>
      </div>
    </main>
  );
}
