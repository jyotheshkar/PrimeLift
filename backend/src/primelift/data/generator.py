"""Synthetic London campaign dataset generation for the first PrimeLift backend slice."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from primelift.data.schema import DATASET_RANDOM_SEED, DATASET_ROW_COUNT, REQUIRED_COLUMNS
from primelift.utils.paths import DEFAULT_DATASET_PATH, ensure_project_directories


@dataclass(frozen=True)
class SegmentProfile:
    """Configuration used to generate realistic user features by segment."""

    weight: float
    age_mean: float
    age_std: float
    engagement_alpha: float
    engagement_beta: float
    sessions_lambda: float
    purchases_lambda: float
    order_value_median: float
    order_value_sigma: float
    tenure_shape: float
    tenure_scale: float
    member_base_probability: float
    gender_weights: dict[str, float]
    device_weights: dict[str, float]
    traffic_weights: dict[str, float]
    baseline_logit_shift: float
    treatment_effect: float
    revenue_multiplier: float
    ios_share: float


BOROUGH_PROFILES: dict[str, dict[str, object]] = {
    "Barking and Dagenham": {"weight": 1.0, "postcode_weights": {"IG": 0.52, "RM": 0.48}},
    "Barnet": {"weight": 2.1, "postcode_weights": {"N": 0.45, "NW": 0.32, "EN": 0.23}},
    "Bexley": {"weight": 1.1, "postcode_weights": {"DA": 0.74, "SE": 0.26}},
    "Brent": {"weight": 1.8, "postcode_weights": {"NW": 0.73, "HA": 0.27}},
    "Bromley": {"weight": 1.9, "postcode_weights": {"BR": 0.76, "SE": 0.24}},
    "Camden": {"weight": 1.5, "postcode_weights": {"NW": 0.42, "WC": 0.33, "N": 0.25}},
    "City of London": {"weight": 0.3, "postcode_weights": {"EC": 0.72, "WC": 0.28}},
    "Croydon": {"weight": 2.2, "postcode_weights": {"CR": 0.78, "SE": 0.22}},
    "Ealing": {"weight": 2.0, "postcode_weights": {"W": 0.34, "UB": 0.66}},
    "Enfield": {"weight": 1.6, "postcode_weights": {"N": 0.52, "EN": 0.48}},
    "Greenwich": {"weight": 1.5, "postcode_weights": {"SE": 0.82, "DA": 0.18}},
    "Hackney": {"weight": 1.7, "postcode_weights": {"E": 0.78, "N": 0.22}},
    "Hammersmith and Fulham": {"weight": 1.3, "postcode_weights": {"W": 0.61, "SW": 0.39}},
    "Haringey": {"weight": 1.4, "postcode_weights": {"N": 0.76, "NW": 0.24}},
    "Harrow": {"weight": 1.2, "postcode_weights": {"HA": 0.86, "NW": 0.14}},
    "Havering": {"weight": 1.3, "postcode_weights": {"RM": 0.88, "IG": 0.12}},
    "Hillingdon": {"weight": 1.5, "postcode_weights": {"UB": 0.71, "HA": 0.29}},
    "Hounslow": {"weight": 1.4, "postcode_weights": {"TW": 0.73, "W": 0.27}},
    "Islington": {"weight": 1.4, "postcode_weights": {"N": 0.58, "EC": 0.42}},
    "Kensington and Chelsea": {"weight": 0.9, "postcode_weights": {"SW": 0.58, "W": 0.42}},
    "Kingston upon Thames": {"weight": 0.8, "postcode_weights": {"KT": 0.84, "SW": 0.16}},
    "Lambeth": {"weight": 1.9, "postcode_weights": {"SE": 0.56, "SW": 0.44}},
    "Lewisham": {"weight": 1.6, "postcode_weights": {"SE": 0.91, "BR": 0.09}},
    "Merton": {"weight": 1.0, "postcode_weights": {"SW": 0.67, "CR": 0.33}},
    "Newham": {"weight": 1.8, "postcode_weights": {"E": 0.81, "IG": 0.19}},
    "Redbridge": {"weight": 1.4, "postcode_weights": {"IG": 0.79, "E": 0.21}},
    "Richmond upon Thames": {"weight": 0.9, "postcode_weights": {"TW": 0.78, "SW": 0.22}},
    "Southwark": {"weight": 1.8, "postcode_weights": {"SE": 0.74, "EC": 0.26}},
    "Sutton": {"weight": 0.9, "postcode_weights": {"SM": 0.72, "CR": 0.28}},
    "Tower Hamlets": {"weight": 1.6, "postcode_weights": {"E": 0.66, "EC": 0.34}},
    "Waltham Forest": {"weight": 1.3, "postcode_weights": {"E": 0.79, "IG": 0.21}},
    "Wandsworth": {"weight": 1.7, "postcode_weights": {"SW": 0.84, "SE": 0.16}},
    "Westminster": {"weight": 1.2, "postcode_weights": {"W": 0.43, "SW": 0.28, "WC": 0.29}},
}

SEGMENT_PROFILES = {
    "Young Professionals": SegmentProfile(
        weight=0.18,
        age_mean=30.0,
        age_std=5.8,
        engagement_alpha=4.6,
        engagement_beta=3.0,
        sessions_lambda=5.8,
        purchases_lambda=1.1,
        order_value_median=86.0,
        order_value_sigma=0.28,
        tenure_shape=2.6,
        tenure_scale=185.0,
        member_base_probability=0.28,
        gender_weights={"female": 0.50, "male": 0.46, "non_binary": 0.04},
        device_weights={"mobile": 0.71, "desktop": 0.22, "tablet": 0.07},
        traffic_weights={
            "direct": 0.19,
            "paid_search": 0.22,
            "organic_search": 0.20,
            "email": 0.10,
            "affiliate": 0.05,
            "social": 0.18,
            "display": 0.06,
        },
        baseline_logit_shift=0.10,
        treatment_effect=0.018,
        revenue_multiplier=1.05,
        ios_share=0.58,
    ),
    "Families": SegmentProfile(
        weight=0.16,
        age_mean=40.0,
        age_std=7.2,
        engagement_alpha=4.3,
        engagement_beta=3.2,
        sessions_lambda=5.1,
        purchases_lambda=1.2,
        order_value_median=93.0,
        order_value_sigma=0.26,
        tenure_shape=3.3,
        tenure_scale=240.0,
        member_base_probability=0.35,
        gender_weights={"female": 0.52, "male": 0.45, "non_binary": 0.03},
        device_weights={"mobile": 0.64, "desktop": 0.24, "tablet": 0.12},
        traffic_weights={
            "direct": 0.20,
            "paid_search": 0.18,
            "organic_search": 0.17,
            "email": 0.20,
            "affiliate": 0.07,
            "social": 0.08,
            "display": 0.10,
        },
        baseline_logit_shift=0.16,
        treatment_effect=0.012,
        revenue_multiplier=1.14,
        ios_share=0.55,
    ),
    "Students": SegmentProfile(
        weight=0.10,
        age_mean=22.0,
        age_std=3.0,
        engagement_alpha=3.0,
        engagement_beta=4.5,
        sessions_lambda=3.8,
        purchases_lambda=0.35,
        order_value_median=47.0,
        order_value_sigma=0.34,
        tenure_shape=1.5,
        tenure_scale=120.0,
        member_base_probability=0.10,
        gender_weights={"female": 0.48, "male": 0.47, "non_binary": 0.05},
        device_weights={"mobile": 0.84, "desktop": 0.10, "tablet": 0.06},
        traffic_weights={
            "direct": 0.10,
            "paid_search": 0.13,
            "organic_search": 0.22,
            "email": 0.05,
            "affiliate": 0.08,
            "social": 0.32,
            "display": 0.10,
        },
        baseline_logit_shift=-0.26,
        treatment_effect=0.004,
        revenue_multiplier=0.88,
        ios_share=0.52,
    ),
    "High Intent Returners": SegmentProfile(
        weight=0.14,
        age_mean=35.0,
        age_std=8.0,
        engagement_alpha=5.8,
        engagement_beta=2.1,
        sessions_lambda=7.4,
        purchases_lambda=1.9,
        order_value_median=98.0,
        order_value_sigma=0.24,
        tenure_shape=3.5,
        tenure_scale=210.0,
        member_base_probability=0.38,
        gender_weights={"female": 0.51, "male": 0.46, "non_binary": 0.03},
        device_weights={"mobile": 0.67, "desktop": 0.25, "tablet": 0.08},
        traffic_weights={
            "direct": 0.31,
            "paid_search": 0.20,
            "organic_search": 0.12,
            "email": 0.19,
            "affiliate": 0.03,
            "social": 0.08,
            "display": 0.07,
        },
        baseline_logit_shift=0.32,
        treatment_effect=0.026,
        revenue_multiplier=1.16,
        ios_share=0.56,
    ),
    "Loyal Members": SegmentProfile(
        weight=0.12,
        age_mean=42.0,
        age_std=9.0,
        engagement_alpha=6.1,
        engagement_beta=2.0,
        sessions_lambda=7.0,
        purchases_lambda=2.2,
        order_value_median=112.0,
        order_value_sigma=0.22,
        tenure_shape=4.0,
        tenure_scale=260.0,
        member_base_probability=0.80,
        gender_weights={"female": 0.54, "male": 0.43, "non_binary": 0.03},
        device_weights={"mobile": 0.60, "desktop": 0.28, "tablet": 0.12},
        traffic_weights={
            "direct": 0.29,
            "paid_search": 0.09,
            "organic_search": 0.18,
            "email": 0.28,
            "affiliate": 0.03,
            "social": 0.05,
            "display": 0.08,
        },
        baseline_logit_shift=0.38,
        treatment_effect=0.001,
        revenue_multiplier=1.22,
        ios_share=0.60,
    ),
    "Bargain Hunters": SegmentProfile(
        weight=0.12,
        age_mean=36.0,
        age_std=9.2,
        engagement_alpha=3.6,
        engagement_beta=3.8,
        sessions_lambda=4.9,
        purchases_lambda=0.9,
        order_value_median=61.0,
        order_value_sigma=0.31,
        tenure_shape=2.3,
        tenure_scale=175.0,
        member_base_probability=0.18,
        gender_weights={"female": 0.53, "male": 0.44, "non_binary": 0.03},
        device_weights={"mobile": 0.73, "desktop": 0.17, "tablet": 0.10},
        traffic_weights={
            "direct": 0.09,
            "paid_search": 0.24,
            "organic_search": 0.12,
            "email": 0.16,
            "affiliate": 0.22,
            "social": 0.07,
            "display": 0.10,
        },
        baseline_logit_shift=-0.05,
        treatment_effect=0.015,
        revenue_multiplier=0.94,
        ios_share=0.53,
    ),
    "Window Shoppers": SegmentProfile(
        weight=0.10,
        age_mean=31.0,
        age_std=8.4,
        engagement_alpha=2.7,
        engagement_beta=5.1,
        sessions_lambda=2.9,
        purchases_lambda=0.18,
        order_value_median=58.0,
        order_value_sigma=0.35,
        tenure_shape=1.8,
        tenure_scale=145.0,
        member_base_probability=0.08,
        gender_weights={"female": 0.49, "male": 0.47, "non_binary": 0.04},
        device_weights={"mobile": 0.79, "desktop": 0.15, "tablet": 0.06},
        traffic_weights={
            "direct": 0.08,
            "paid_search": 0.13,
            "organic_search": 0.15,
            "email": 0.05,
            "affiliate": 0.05,
            "social": 0.31,
            "display": 0.23,
        },
        baseline_logit_shift=-0.42,
        treatment_effect=-0.004,
        revenue_multiplier=0.90,
        ios_share=0.54,
    ),
    "Lapsed Users": SegmentProfile(
        weight=0.08,
        age_mean=45.0,
        age_std=10.0,
        engagement_alpha=2.2,
        engagement_beta=5.7,
        sessions_lambda=2.2,
        purchases_lambda=0.25,
        order_value_median=76.0,
        order_value_sigma=0.30,
        tenure_shape=3.0,
        tenure_scale=300.0,
        member_base_probability=0.16,
        gender_weights={"female": 0.51, "male": 0.46, "non_binary": 0.03},
        device_weights={"mobile": 0.62, "desktop": 0.27, "tablet": 0.11},
        traffic_weights={
            "direct": 0.12,
            "paid_search": 0.09,
            "organic_search": 0.07,
            "email": 0.26,
            "affiliate": 0.05,
            "social": 0.06,
            "display": 0.35,
        },
        baseline_logit_shift=-0.48,
        treatment_effect=-0.008,
        revenue_multiplier=1.01,
        ios_share=0.57,
    ),
}

SOURCE_CHANNELS = {
    "direct": {"homepage": 0.47, "app_entry": 0.31, "brand_navigation": 0.22},
    "paid_search": {"brand_search": 0.41, "generic_search": 0.59},
    "organic_search": {"seo_brand": 0.34, "seo_content": 0.66},
    "email": {"lifecycle_email": 0.56, "promo_email": 0.44},
    "affiliate": {"affiliate_content": 0.43, "cashback_partner": 0.57},
    "social": {"paid_social": 0.72, "organic_social": 0.28},
    "display": {"retargeting_display": 0.64, "prospecting_display": 0.36},
}

SOURCE_CAMPAIGNS = {
    "direct": "PL-LON-RETENTION-2026-01",
    "paid_search": "PL-LON-SEARCH-2026-01",
    "organic_search": "PL-LON-SEO-HALO-2026-01",
    "email": "PL-LON-CRM-2026-01",
    "affiliate": "PL-LON-AFFILIATE-2026-01",
    "social": "PL-LON-SOCIAL-2026-01",
    "display": "PL-LON-DISPLAY-2026-01",
}

SOURCE_EFFECTS = {
    "direct": 0.22,
    "paid_search": 0.13,
    "organic_search": 0.07,
    "email": 0.18,
    "affiliate": 0.04,
    "social": -0.05,
    "display": -0.13,
}

DEVICE_EFFECTS = {"mobile": 0.00, "desktop": 0.05, "tablet": 0.02}


def _sample_from_weight_map(
    rng: np.random.Generator, weight_map: dict[str, float], size: int
) -> np.ndarray:
    """Sample string categories from a weight map."""

    categories = np.array(list(weight_map.keys()), dtype=object)
    weights = np.array(list(weight_map.values()), dtype=float)
    probabilities = weights / weights.sum()
    return rng.choice(categories, size=size, p=probabilities)


def _generate_platforms(
    rng: np.random.Generator, device_types: np.ndarray, ios_share: float
) -> np.ndarray:
    """Generate a realistic platform mix aligned to the observed device type."""

    platforms = np.empty(device_types.shape[0], dtype=object)

    desktop_mask = device_types == "desktop"
    mobile_mask = device_types == "mobile"
    tablet_mask = device_types == "tablet"

    platforms[desktop_mask] = "web"
    platforms[mobile_mask] = rng.choice(
        np.array(["ios", "android"], dtype=object),
        size=mobile_mask.sum(),
        p=[ios_share, 1.0 - ios_share],
    )
    tablet_ios_share = min(max(ios_share - 0.08, 0.35), 0.70)
    tablet_android_share = min(max(0.20, 1.0 - tablet_ios_share - 0.18), 0.45)
    tablet_web_share = 1.0 - tablet_ios_share - tablet_android_share
    platforms[tablet_mask] = rng.choice(
        np.array(["ios", "android", "web"], dtype=object),
        size=tablet_mask.sum(),
        p=[tablet_ios_share, tablet_android_share, tablet_web_share],
    )
    return platforms


def _generate_channels(rng: np.random.Generator, sources: np.ndarray) -> np.ndarray:
    """Generate a nested marketing channel for each traffic source."""

    channels = np.empty(sources.shape[0], dtype=object)
    for source, channel_weights in SOURCE_CHANNELS.items():
        indices = np.flatnonzero(sources == source)
        if indices.size == 0:
            continue
        channels[indices] = _sample_from_weight_map(rng, channel_weights, indices.size)
    return channels


def _generate_event_dates(rng: np.random.Generator, size: int) -> np.ndarray:
    """Generate recent event dates over an eight week window."""

    date_range = pd.date_range("2026-02-01", "2026-03-02", freq="D")
    weekday_weights = np.where(date_range.weekday < 5, 1.0, 0.74)
    recency_weights = np.linspace(0.92, 1.14, num=date_range.size)
    probabilities = weekday_weights * recency_weights
    probabilities = probabilities / probabilities.sum()
    selected_dates = rng.choice(date_range.to_numpy(), size=size, p=probabilities)
    return pd.to_datetime(selected_dates).strftime("%Y-%m-%d").to_numpy(dtype=object)


def _assign_age_band(ages: np.ndarray) -> np.ndarray:
    """Bucket user ages into business-friendly age bands."""

    age_band = pd.cut(
        ages,
        bins=[17, 24, 34, 44, 54, 64, 120],
        labels=["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
    )
    return np.asarray(age_band.astype(str), dtype=object)


def _sigmoid(values: np.ndarray) -> np.ndarray:
    """Compute a numerically stable sigmoid."""

    clipped = np.clip(values, -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def generate_london_campaign_users(
    row_count: int = DATASET_ROW_COUNT, seed: int = DATASET_RANDOM_SEED
) -> pd.DataFrame:
    """Generate a reproducible London campaign dataset for experimentation analysis."""

    if row_count <= 0:
        raise ValueError("row_count must be positive")

    rng = np.random.default_rng(seed)

    segment_weights = {name: profile.weight for name, profile in SEGMENT_PROFILES.items()}
    borough_weights = {
        borough: float(profile["weight"]) for borough, profile in BOROUGH_PROFILES.items()
    }

    segments = _sample_from_weight_map(rng, segment_weights, row_count)
    boroughs = _sample_from_weight_map(rng, borough_weights, row_count)

    postcode_areas = np.empty(row_count, dtype=object)
    ages = np.empty(row_count, dtype=int)
    genders = np.empty(row_count, dtype=object)
    device_types = np.empty(row_count, dtype=object)
    platforms = np.empty(row_count, dtype=object)
    traffic_sources = np.empty(row_count, dtype=object)
    channels = np.empty(row_count, dtype=object)
    engagement_scores = np.empty(row_count, dtype=float)
    prior_purchases = np.empty(row_count, dtype=int)
    prior_sessions = np.empty(row_count, dtype=int)
    avg_order_values = np.empty(row_count, dtype=float)
    tenures = np.empty(row_count, dtype=int)
    prime_members = np.empty(row_count, dtype=int)

    for borough_name, borough_profile in BOROUGH_PROFILES.items():
        borough_indices = np.flatnonzero(boroughs == borough_name)
        if borough_indices.size == 0:
            continue
        postcode_areas[borough_indices] = _sample_from_weight_map(
            rng,
            borough_profile["postcode_weights"],
            borough_indices.size,
        )

    for segment_name, profile in SEGMENT_PROFILES.items():
        indices = np.flatnonzero(segments == segment_name)
        if indices.size == 0:
            continue

        segment_engagement = np.clip(
            rng.beta(profile.engagement_alpha, profile.engagement_beta, size=indices.size)
            * 100.0,
            1.0,
            99.0,
        )
        segment_tenure = np.clip(
            rng.gamma(profile.tenure_shape, profile.tenure_scale, size=indices.size),
            7.0,
            3650.0,
        ).astype(int)
        membership_probability = np.clip(
            profile.member_base_probability
            + np.where(segment_engagement >= 72.0, 0.10, 0.00)
            + np.where(segment_tenure >= 540, 0.08, 0.00)
            - np.where(segment_engagement <= 25.0, 0.06, 0.00),
            0.02,
            0.96,
        )
        segment_members = rng.binomial(1, membership_probability).astype(int)

        session_lambda = np.clip(
            profile.sessions_lambda
            * (0.65 + segment_engagement / 100.0)
            * (0.80 + np.log1p(segment_tenure) / 6.5)
            * (1.00 + 0.10 * segment_members),
            0.15,
            45.0,
        )
        segment_sessions = np.clip(rng.poisson(session_lambda), 0, 120).astype(int)

        purchase_lambda = np.clip(
            profile.purchases_lambda
            * (0.55 + segment_engagement / 120.0)
            * (1.00 + 0.12 * segment_members)
            * (1.00 + 0.04 * np.log1p(segment_sessions)),
            0.02,
            12.0,
        )
        segment_purchases = np.clip(rng.poisson(purchase_lambda), 0, 25).astype(int)

        raw_order_value = rng.lognormal(
            mean=np.log(profile.order_value_median),
            sigma=profile.order_value_sigma,
            size=indices.size,
        )
        segment_order_value = np.clip(
            raw_order_value
            * (1.00 + 0.03 * np.minimum(segment_purchases, 4))
            * (1.00 + 0.04 * segment_members),
            12.0,
            420.0,
        )

        segment_device_types = _sample_from_weight_map(rng, profile.device_weights, indices.size)
        segment_traffic_sources = _sample_from_weight_map(
            rng, profile.traffic_weights, indices.size
        )

        ages[indices] = np.clip(
            np.rint(rng.normal(profile.age_mean, profile.age_std, size=indices.size)),
            18,
            78,
        ).astype(int)
        genders[indices] = _sample_from_weight_map(rng, profile.gender_weights, indices.size)
        device_types[indices] = segment_device_types
        platforms[indices] = _generate_platforms(rng, segment_device_types, profile.ios_share)
        traffic_sources[indices] = segment_traffic_sources
        channels[indices] = _generate_channels(rng, segment_traffic_sources)
        engagement_scores[indices] = segment_engagement
        prior_purchases[indices] = segment_purchases
        prior_sessions[indices] = segment_sessions
        avg_order_values[indices] = segment_order_value
        tenures[indices] = segment_tenure
        prime_members[indices] = segment_members

    age_bands = _assign_age_band(ages)
    treatment = rng.binomial(1, 0.5, row_count).astype(int)

    source_effect = np.array([SOURCE_EFFECTS[source] for source in traffic_sources], dtype=float)
    device_effect = np.array([DEVICE_EFFECTS[device] for device in device_types], dtype=float)
    segment_logit_shift = np.array(
        [SEGMENT_PROFILES[segment].baseline_logit_shift for segment in segments], dtype=float
    )
    segment_treatment_effect = np.array(
        [SEGMENT_PROFILES[segment].treatment_effect for segment in segments], dtype=float
    )
    segment_revenue_multiplier = np.array(
        [SEGMENT_PROFILES[segment].revenue_multiplier for segment in segments], dtype=float
    )
    age_effect = np.select(
        [ages < 25, ages < 35, ages < 45, ages < 55, ages < 65],
        [-0.10, 0.05, 0.12, 0.06, -0.01],
        default=-0.08,
    )

    base_logit = (
        -4.15
        + 0.62 * ((engagement_scores - 50.0) / 20.0)
        + 0.18 * np.log1p(prior_sessions)
        + 0.34 * np.log1p(prior_purchases)
        + 0.14 * (avg_order_values / 100.0)
        + 0.18 * np.log1p(tenures / 180.0)
        + 0.36 * prime_members
        + source_effect
        + device_effect
        + age_effect
        + segment_logit_shift
    )
    baseline_probability = np.clip(_sigmoid(base_logit), 0.003, 0.45)

    treatment_effect = segment_treatment_effect.copy()
    treatment_effect += np.where(
        np.isin(traffic_sources, np.array(["email", "paid_search"], dtype=object)), 0.0035, 0.0
    )
    treatment_effect += np.where(engagement_scores >= 75.0, 0.0030, 0.0)
    treatment_effect += np.where(
        (segments == "Bargain Hunters")
        & np.isin(traffic_sources, np.array(["affiliate", "email"], dtype=object)),
        0.0060,
        0.0,
    )
    treatment_effect -= np.where(
        (segments == "Lapsed Users") & (traffic_sources == "display"), 0.0050, 0.0
    )
    treatment_effect -= np.where(
        (segments == "Window Shoppers") & (traffic_sources == "social"), 0.0025, 0.0
    )
    treatment_effect = np.clip(treatment_effect, -0.03, 0.08)

    conversion_probability = np.clip(
        baseline_probability + treatment * treatment_effect,
        0.001,
        0.75,
    )
    conversion = rng.binomial(1, conversion_probability).astype(int)

    revenue_noise = rng.lognormal(mean=0.0, sigma=0.24, size=row_count)
    revenue = np.where(
        conversion == 1,
        np.clip(
            avg_order_values
            * segment_revenue_multiplier
            * revenue_noise
            * (1.00 + 0.05 * prime_members)
            * (1.00 + 0.03 * np.minimum(prior_purchases, 3)),
            8.0,
            650.0,
        ),
        0.0,
    )

    campaign_id = np.array([SOURCE_CAMPAIGNS[source] for source in traffic_sources], dtype=object)
    event_dates = _generate_event_dates(rng, row_count)

    dataset = pd.DataFrame(
        {
            "user_id": [f"LON-{index:06d}" for index in range(1, row_count + 1)],
            "london_borough": boroughs,
            "postcode_area": postcode_areas,
            "age": ages,
            "age_band": age_bands,
            "gender": genders,
            "device_type": device_types,
            "platform": platforms,
            "traffic_source": traffic_sources,
            "channel": channels,
            "prior_engagement_score": np.round(engagement_scores, 1),
            "prior_purchases_90d": prior_purchases,
            "prior_sessions_30d": prior_sessions,
            "avg_order_value": np.round(avg_order_values, 2),
            "customer_tenure_days": tenures,
            "is_prime_like_member": prime_members,
            "segment": segments,
            "treatment": treatment,
            "conversion": conversion,
            "revenue": np.round(revenue, 2),
            "campaign_id": campaign_id,
            "event_date": event_dates,
        }
    )[REQUIRED_COLUMNS]

    return dataset


def save_dataset(dataset: pd.DataFrame, output_path: Path) -> Path:
    """Persist a generated dataset to CSV."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False)
    return output_path


def generate_and_save_default_dataset(
    row_count: int = DATASET_ROW_COUNT, seed: int = DATASET_RANDOM_SEED
) -> Path:
    """Generate and save the default 100k London campaign dataset."""

    ensure_project_directories()
    dataset = generate_london_campaign_users(row_count=row_count, seed=seed)
    return save_dataset(dataset, DEFAULT_DATASET_PATH)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate the synthetic PrimeLift London campaign dataset."
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=DATASET_ROW_COUNT,
        help="Number of rows to generate. Defaults to 100000.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DATASET_RANDOM_SEED,
        help="Random seed for reproducible output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Output CSV path.",
    )
    return parser


def main() -> None:
    """CLI entrypoint for dataset generation."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    ensure_project_directories()
    dataset = generate_london_campaign_users(row_count=args.rows, seed=args.seed)
    output_path = save_dataset(dataset, args.output)
    print(f"Wrote {len(dataset):,} rows to {output_path}")


if __name__ == "__main__":
    main()
