export const overviewSnapshot = {
  headline: {
    label: "London causal decision engine",
    title: "PrimeLift AI surfaces who to influence, who to suppress, and where the next pound should go.",
    description:
      "This first dashboard slice is a static overview snapshot based on the saved backend artifacts from Phases 3 to 6. Live API integration comes in Phase 8.",
  },
  kpis: [
    {
      label: "Baseline ATE",
      value: "+1.02pp",
      detail: "Conversion lift from the saved 100k London experiment baseline.",
      accent: "teal",
    },
    {
      label: "Champion Model",
      value: "DRLearner",
      detail: "Current conversion winner from the Phase 3 comparison report.",
      accent: "amber",
    },
    {
      label: "Top Uplift Segment",
      value: "High Intent Returners",
      detail: "Observed segment lift +2.43pp in the saved Phase 4 rollup.",
      accent: "slate",
    },
    {
      label: "Budget Lead",
      value: "37.9%",
      detail: "Recommended share for High Intent Returners from Phase 5.",
      accent: "coral",
    },
  ],
  systemState: {
    policyChampion: "DRPolicyForest",
    policyValue: "0.1235",
    validationVerdict: "promising_but_noisy",
    testSplit: "test",
    note: "The ranking is useful enough to act on, but not ordered cleanly end to end.",
  },
  topSegments: [
    { name: "High Intent Returners", uplift: 2.43, budget: 37.9 },
    { name: "Bargain Hunters", uplift: 2.32, budget: 5.7 },
    { name: "Young Professionals", uplift: 1.54, budget: 14.1 },
    { name: "Students", uplift: 0.95, budget: 4.6 },
  ],
  suppressionWatch: [
    { name: "Lapsed Users", signal: "-0.80pp observed lift", note: "Zero incremental budget." },
    { name: "app_entry", signal: "-2.39pp observed lift", note: "Suppress or deprioritize." },
    { name: "Camden", signal: "-2.93pp observed lift", note: "Weak borough-level response." },
  ],
  recommendation: {
    summary:
      "Use DRPolicyForest as the current policy champion. Prioritize High Intent Returners, Loyal Members, Young Professionals; suppress Lapsed Users.",
    targetUsers: 10,
    suppressUsers: 10,
    source: "Saved Phase 5 decision closeout artifact",
  },
  readiness: [
    { phase: "Phase 3", status: "Complete", item: "Causal ML training and model comparison" },
    { phase: "Phase 4", status: "Complete", item: "Model-based uplift rollups and validation" },
    { phase: "Phase 5", status: "Complete", item: "Policy learning, budgeting, and closeout" },
    { phase: "Phase 6", status: "Complete", item: "Dataset and analysis API endpoints" },
  ],
  nextUp: [
    "Wire this overview to live FastAPI endpoints in Phase 8.",
    "Add segment charts, scored tables, and recommendation panels as dedicated routes.",
    "Expose dataset preview and model registry panels from the frontend shell.",
  ],
} as const;
