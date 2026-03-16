export const datasetModelsSnapshot = {
  header: {
    eyebrow: "Phase 2 and Phase 3 asset view",
    title: "The data contract, feature pipeline, and trained model registry are ready for integration.",
    description:
      "This screen is a static rendering of the saved dataset, preparation manifest, and model comparison artifacts. It shows what data exists, how it is shaped for training, and which models are already in service.",
  },
  dataset: {
    rowCount: "100,000",
    columnCount: 22,
    rawFeatureCount: 16,
    transformedFeatureCount: 105,
    splitSummary: [
      { name: "Train", rows: "70,000", rate: "11.78% conversion" },
      { name: "Validation", rows: "15,000", rate: "11.78% conversion" },
      { name: "Test", rows: "15,000", rate: "11.77% conversion" },
    ],
    schemaGroups: [
      { label: "Identifier", count: 2, columns: ["user_id", "campaign_id"] },
      { label: "Date", count: 1, columns: ["event_date"] },
      { label: "Treatment", count: 1, columns: ["treatment"] },
      { label: "Outcomes", count: 2, columns: ["conversion", "revenue"] },
      {
        label: "Categorical features",
        count: 10,
        columns: ["london_borough", "postcode_area", "age_band", "gender", "device_type"],
      },
      {
        label: "Numeric features",
        count: 6,
        columns: ["age", "prior_engagement_score", "prior_purchases_90d", "prior_sessions_30d"],
      },
    ],
    sampleRows: [
      {
        userId: "LON-000001",
        borough: "Wandsworth",
        segment: "Bargain Hunters",
        treatment: 0,
        conversion: 0,
        revenue: "0.00",
      },
      {
        userId: "LON-000002",
        borough: "Wandsworth",
        segment: "Students",
        treatment: 0,
        conversion: 0,
        revenue: "0.00",
      },
      {
        userId: "LON-000003",
        borough: "Hillingdon",
        segment: "Window Shoppers",
        treatment: 0,
        conversion: 0,
        revenue: "0.00",
      },
      {
        userId: "LON-000004",
        borough: "Croydon",
        segment: "Loyal Members",
        treatment: 1,
        conversion: 0,
        revenue: "0.00",
      },
      {
        userId: "LON-000005",
        borough: "Newham",
        segment: "Young Professionals",
        treatment: 0,
        conversion: 0,
        revenue: "0.00",
      },
    ],
  },
  modelRegistry: [
    {
      name: "ATE baseline",
      family: "baseline",
      status: "implemented",
      role: "scientific sanity check",
    },
    {
      name: "XLearner conversion",
      family: "cate",
      status: "implemented",
      role: "ML uplift baseline",
    },
    {
      name: "DRLearner conversion",
      family: "cate",
      status: "implemented",
      role: "conversion champion",
    },
    {
      name: "DRLearner revenue",
      family: "cate",
      status: "implemented",
      role: "revenue champion",
    },
    {
      name: "CausalForestDML",
      family: "cate",
      status: "implemented",
      role: "challenger",
    },
    {
      name: "DRPolicyTree",
      family: "policy",
      status: "implemented",
      role: "explainable policy",
    },
    {
      name: "DRPolicyForest",
      family: "policy",
      status: "implemented",
      role: "policy champion",
    },
  ],
  modelSelection: {
    conversionChampion: "DRLearner conversion",
    conversionChallenger: "CausalForestDML conversion",
    revenueChampion: "DRLearner revenue",
    policyChampion: "DRPolicyForest",
  },
  trainingStatus: [
    {
      label: "Dataset generation",
      status: "Complete",
      detail: "London campaign dataset saved at 100k rows.",
    },
    {
      label: "Feature preparation",
      status: "Complete",
      detail: "Preprocessor artifact and model-ready splits are saved.",
    },
    {
      label: "Model comparison",
      status: "Complete",
      detail: "Champion/challenger selection already saved to Phase 3 report.",
    },
    {
      label: "Policy closeout",
      status: "Complete",
      detail: "Budget and recommendation outputs are available from Phase 5.",
    },
    {
      label: "Frontend integration",
      status: "Pending",
      detail: "Buttons stay non-live until Phase 8 API wiring.",
    },
  ],
} as const;
