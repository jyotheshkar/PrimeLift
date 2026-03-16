export const recommendationsSnapshot = {
  header: {
    eyebrow: "Phase 5 ML decision engine",
    title: "PrimeLift turns uplift into an operational plan: who to scale, who to hold back, and what budget split the current policy prefers.",
    description:
      "This screen is a static rendering of the saved Phase 5 closeout artifacts. It shows the current policy winner, the segment budget plan, and the highest-confidence target and suppression actions.",
  },
  champion: {
    modelName: "DRPolicyForest",
    value: 0.1235,
    gainOverRunnerUp: 0.0008,
    gainOverAlwaysControl: 0.0107,
    reason:
      "DRPolicyForest is the current champion because it beats the policy tree and both naive baselines on the holdout split.",
  },
  finalSummary:
    "Use DRPolicyForest as the current policy champion. Prioritize High Intent Returners, Loyal Members, Young Professionals; suppress Lapsed Users.",
  budgetPlan: [
    {
      segment: "High Intent Returners",
      budgetShare: 37.87,
      budgetAmount: 37869.54,
      conversionEffect: 2.2911,
      revenueEffect: 3.0546,
      policyAlignment: "champion_policy_treat",
    },
    {
      segment: "Loyal Members",
      budgetShare: 23.93,
      budgetAmount: 23925.97,
      conversionEffect: 0.3909,
      revenueEffect: 0.4163,
      policyAlignment: "champion_policy_holdout",
    },
    {
      segment: "Young Professionals",
      budgetShare: 14.06,
      budgetAmount: 14055.22,
      conversionEffect: 1.2843,
      revenueEffect: 1.1214,
      policyAlignment: "champion_policy_treat",
    },
    {
      segment: "Families",
      budgetShare: 9.47,
      budgetAmount: 9473.05,
      conversionEffect: 0.6968,
      revenueEffect: 0.6075,
      policyAlignment: "champion_policy_treat",
    },
    {
      segment: "Bargain Hunters",
      budgetShare: 5.67,
      budgetAmount: 5666.59,
      conversionEffect: 1.5572,
      revenueEffect: 0.878,
      policyAlignment: "neutral",
    },
  ],
  suppressedSegments: [
    {
      segment: "Lapsed Users",
      observedAte: -0.8005,
      revenueEffect: 0.7045,
      budgetAmount: 0,
      policyAlignment: "champion_policy_holdout",
    },
  ],
  targetUsers: [
    {
      userId: "LON-065845",
      segment: "High Intent Returners",
      borough: "Hackney",
      predictedEffect: 42.88,
    },
    {
      userId: "LON-049529",
      segment: "High Intent Returners",
      borough: "Merton",
      predictedEffect: 42.01,
    },
    {
      userId: "LON-083860",
      segment: "High Intent Returners",
      borough: "Hackney",
      predictedEffect: 37.33,
    },
    {
      userId: "LON-095017",
      segment: "High Intent Returners",
      borough: "Brent",
      predictedEffect: 36.94,
    },
    {
      userId: "LON-079852",
      segment: "Loyal Members",
      borough: "Hillingdon",
      predictedEffect: 30.03,
    },
  ],
  suppressUsers: [
    {
      userId: "LON-038770",
      segment: "High Intent Returners",
      borough: "Islington",
      predictedEffect: -26.52,
    },
    {
      userId: "LON-056125",
      segment: "High Intent Returners",
      borough: "Tower Hamlets",
      predictedEffect: -22.68,
    },
    {
      userId: "LON-085976",
      segment: "High Intent Returners",
      borough: "Barnet",
      predictedEffect: -21.68,
    },
    {
      userId: "LON-037833",
      segment: "High Intent Returners",
      borough: "Brent",
      predictedEffect: -20.83,
    },
    {
      userId: "LON-091916",
      segment: "High Intent Returners",
      borough: "Hackney",
      predictedEffect: -20.52,
    },
  ],
  notes: [
    "The policy champion is ML-driven rather than a naive always-treat baseline.",
    "Budget is concentrated in a few segments, with High Intent Returners taking the largest share.",
    "The closeout report still shows some nuanced policy behavior, like holding out Loyal Members and Window Shoppers in parts of the tree/forest logic.",
  ],
} as const;
