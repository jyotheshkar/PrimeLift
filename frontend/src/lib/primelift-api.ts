const DEFAULT_API_URL = "http://127.0.0.1:8000";

export function getPrimeLiftApiUrl() {
  return process.env.NEXT_PUBLIC_PRIMELIFT_API_URL ?? DEFAULT_API_URL;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getPrimeLiftApiUrl()}${path}`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`PrimeLift API request failed for ${path} with ${response.status}`);
  }

  return (await response.json()) as T;
}

export type HealthResponse = {
  status: string;
  service_name: string;
  api_version: string;
  current_phase: number;
  timestamp_utc: string;
  readiness: {
    dataset_ready: boolean;
    prepared_data_ready: boolean;
    phase5_closeout_ready: boolean;
  };
};

export type AnalysisATEResponse = {
  result: {
    ate: number;
  };
};

export type AnalysisModelsResponse = {
  status: string;
  report_name: string;
  comparison_split: string;
  conversion_champion_model_name: string;
  conversion_challenger_model_name: string | null;
  revenue_champion_model_name: string;
};

export type AnalysisSegmentsResponse = {
  status: string;
  decile_report_path: string;
  rollup_report_path: string;
  validation_report_path: string;
  model_name: string;
  outcome_column: string;
  split_name: string;
  overall_observed_ate: number;
  top_decile_observed_ate: number | null;
  bottom_decile_observed_ate: number | null;
  top_decile_gain_over_overall_ate: number | null;
  uplift_concentration_ratio: number | null;
  positive_decile_count: number;
  negative_decile_count: number;
  best_decile_rank: number | null;
  worst_decile_rank: number | null;
  monotonicity_break_count: number;
  validation_verdict: string;
  validation_reason: string;
  top_persuadable_deciles: number[];
  suppression_candidate_deciles: number[];
  top_persuadable_cohorts: Array<{
    group_column: string;
    group_value: string;
    mean_predicted_effect: number;
    observed_ate: number;
  }>;
  suppression_candidates: Array<{
    group_column: string;
    group_value: string;
    mean_predicted_effect: number;
    observed_ate: number;
  }>;
  reports: Array<{
    group_column: string;
    top_positive_groups: string[];
    results: Array<{
      group_value: string;
      mean_predicted_effect?: number;
      positive_effect_share?: number;
      observed_ate: number | null;
      recommendation_label?: string;
    }>;
  }>;
  deciles: Array<{
    decile_rank: number;
    observed_ate: number | null;
  }>;
  dimension_summaries: Array<{
    group_column: string;
    top_positive_groups: string[];
  }>;
};

export type AnalysisRecommendationsResponse = {
  status: string;
  policy_champion_model_name: string;
  policy_champion_value: number;
  champion_is_ml_model: boolean;
  final_action_summary: string;
  prioritized_segment_count: number;
  suppressed_segment_count: number;
  top_target_user_count: number;
  top_suppress_user_count: number;
  report: {
    prioritized_segments: Array<{
      segment: string;
      budget_share: number;
      observed_conversion_ate: number | null;
    }>;
    suppressed_segments: Array<{
      segment: string;
      observed_conversion_ate: number | null;
    }>;
  };
};

export async function fetchOverviewBundle() {
  const [health, ate, models, segments, recommendations] = await Promise.all([
    getJson<HealthResponse>("/health"),
    getJson<AnalysisATEResponse>("/analysis/ate?outcome=conversion&bootstrap_samples=120"),
    getJson<AnalysisModelsResponse>("/analysis/models"),
    getJson<AnalysisSegmentsResponse>("/analysis/segments"),
    getJson<AnalysisRecommendationsResponse>("/analysis/recommendations"),
  ]);

  return {
    health,
    ate,
    models,
    segments,
    recommendations,
  };
}

export async function fetchUpliftInsightsData() {
  return getJson<AnalysisSegmentsResponse>("/analysis/segments");
}
