"""Wave parameter converter from affect_state."""

import math

from affect_wave.state.schemas import AffectState, WaveParameter


def convert_to_wave_parameter(state: AffectState) -> WaveParameter:
    """Convert affect_state to wave_parameter deterministically.

    The mapping follows specification:
    - amplitude <- trend.arousal (with dominant emotion boost)
    - frequency <- appraisal.uncertainty + trend.arousal
    - jitter <- concept conflict + risk_flags.instability
    - glow <- appraisal.social_reward + positive(trend.valence)
    - afterglow <- trend.stability + signed(trend.valence) residual
    - density <- concept variance + appraisal simultaneous activation

    Args:
        state: AffectState to convert.

    Returns:
        WaveParameter with all values in 0.0-1.0 range.
    """
    wave = WaveParameter()

    # Amplitude: base from arousal, boosted by dominant emotion intensity
    dominant_intensity = (
        state.top_emotions[0].score if state.top_emotions else 0.5
    )
    wave.amplitude = state.trend.arousal * 0.7 + dominant_intensity * 0.3

    # Frequency: uncertainty and arousal combined
    wave.frequency = (
        state.appraisal.uncertainty * 0.5 +
        state.trend.arousal * 0.3 +
        state.appraisal.novelty * 0.2
    )

    # Jitter: concept conflict + instability
    # Concept conflict = how many concepts have similar high scores
    concept_conflict = _compute_concept_conflict(state.concept_scores)
    inverse_stability = 1.0 - state.trend.stability
    raw_jitter = (
        concept_conflict * 0.4 +
        state.risk_flags.instability * 0.3 +
        inverse_stability * 0.3
    )
    wave.jitter = _compress_high_end(raw_jitter, midpoint=0.58, slope=0.14)

    # Glow: social reward and positive valence
    positive_valence = max(0.0, state.trend.valence)
    wave.glow = (
        state.appraisal.social_reward * 0.4 +
        positive_valence * 0.4 +
        state.appraisal.control * 0.2
    )

    # Afterglow: stability and valence residual
    # Positive valence adds lingering, negative adds tension
    valence_residual = abs(state.trend.valence) * 0.3
    wave.afterglow = (
        state.trend.stability * 0.5 +
        valence_residual +
        (1.0 - state.appraisal.threat) * 0.2
    )

    # Density: canonical spread + concentrated activation
    concept_variance = _compute_concept_variance(state.concept_scores)

    # Count active appraisals (threshold 0.3)
    active_appraisals = sum(
        1 for score in [
            state.appraisal.threat,
            state.appraisal.uncertainty,
            state.appraisal.goal_blockage,
            state.appraisal.social_reward,
            state.appraisal.novelty,
        ]
        if score > 0.3
    )
    appraisal_density = active_appraisals / 5.0

    raw_density = concept_variance * 0.7 + appraisal_density * 0.2 + wave.frequency * 0.1
    wave.density = _compress_high_end(raw_density, midpoint=0.62, slope=0.18)

    # Clamp all values
    wave.clamp_all()

    return wave


def _compute_concept_conflict(concept_scores: list) -> float:
    """Compute concept conflict (how many concepts compete for dominance).

    High conflict = many concepts with similar high scores.
    Low conflict = one concept clearly dominates.

    Args:
        concept_scores: List of ConceptScore objects.

    Returns:
        Conflict value 0.0-1.0.
    """
    if not concept_scores or len(concept_scores) < 2:
        return 0.0

    # Get top 10 concepts
    top_concepts = sorted(concept_scores, key=lambda c: c.score, reverse=True)[:10]

    if len(top_concepts) < 2:
        return 0.0

    # Conflict = how similar are the top scores
    top_score = top_concepts[0].score
    second_score = top_concepts[1].score

    # High conflict if top scores are close
    score_gap = top_score - second_score
    conflict = max(0.0, 1.0 - score_gap * 2)

    # Also consider how many concepts have high scores (> 0.5)
    high_score_count = sum(1 for c in top_concepts if c.score > 0.5)
    spread_factor = min(1.0, high_score_count / 5.0)

    return conflict * 0.6 + spread_factor * 0.4


def _compute_concept_variance(concept_scores: list) -> float:
    """Compute concept variance (spread of concept activation).

    High variance = concepts are spread across different emotions.
    Low variance = concepts concentrated in one emotion.

    Args:
        concept_scores: List of ConceptScore objects.

    Returns:
        Variance value 0.0-1.0.
    """
    if not concept_scores:
        return 0.5

    top_concepts = sorted(concept_scores, key=lambda c: c.score, reverse=True)[:16]
    if not top_concepts:
        return 0.5

    canonical_mass: dict[str, float] = {}
    total = 0.0
    for cs in top_concepts:
        clipped = max(0.0, cs.score - 0.62)
        canonical_mass[cs.canonical] = canonical_mass.get(cs.canonical, 0.0) + clipped
        total += clipped

    if total <= 0:
        return 0.35

    probabilities = [mass / total for mass in canonical_mass.values() if mass > 0]
    entropy = -sum(p * math.log(p, 2) for p in probabilities if p > 0)
    max_entropy = math.log(len(probabilities), 2) if len(probabilities) > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    canonical_spread = min(1.0, len(canonical_mass) / 6.0)
    strongest_mass = max(probabilities) if probabilities else 0.0
    dominance_penalty = max(0.0, strongest_mass - 0.34)
    activation_ratio = sum(1 for cs in top_concepts if cs.score > 0.76) / len(top_concepts)
    score_spread = max(0.0, top_concepts[0].score - top_concepts[-1].score)

    density = (
        normalized_entropy * 0.38 +
        canonical_spread * 0.18 +
        activation_ratio * 0.16 +
        score_spread * 0.18 -
        dominance_penalty * 0.40
    )
    return max(0.0, min(1.0, density))


def render_wave_text(wave: WaveParameter, mode: str = "wave") -> str:
    """Render wave parameter to text representation.

    Args:
        wave: WaveParameter to render.
        mode: Output mode ("wave" or "params").

    Returns:
        Text representation.
    """
    if mode == "params":
        # JSON format for params mode
        import json
        return json.dumps(wave.to_dict(), indent=2)

    segments = int(round(4 + wave.amplitude * 7 + wave.density * 5))
    segment_chars = _select_wave_chars(wave)
    spacing = _select_spacing(wave.frequency)
    glow_prefix, glow_suffix = _select_glow_markers(wave.glow)
    afterglow_suffix = _select_afterglow_suffix(wave.afterglow, wave.jitter)

    pattern = spacing.join(segment_chars[i % len(segment_chars)] for i in range(segments))
    tone_hint = _select_tone_hint(wave)

    return f"{glow_prefix}{pattern}{glow_suffix}{afterglow_suffix}{tone_hint}"


def _select_wave_chars(wave: WaveParameter) -> list[str]:
    """Select visible wave glyphs from jitter and density."""
    if wave.jitter >= 0.84:
        return ["~", "!", "^", "~", ":"]
    if wave.jitter >= 0.66:
        return ["~", "^", "~", ":"]
    if wave.jitter >= 0.44:
        return ["~", "^", "~"]
    if wave.density >= 0.68:
        return ["≈", "~", "≈"]
    if wave.frequency >= 0.7:
        return ["~", "-", "~", "-"]
    return ["~", "~"]


def _select_spacing(frequency: float) -> str:
    """Map frequency to textual spacing."""
    if frequency >= 0.82:
        return ""
    if frequency >= 0.66:
        return " "
    return "  "


def _select_glow_markers(glow: float) -> tuple[str, str]:
    """Map glow to prefix and suffix markers."""
    if glow >= 0.7:
        return ("* ", " *")
    if glow >= 0.52:
        return ("+ ", "")
    if glow <= 0.22:
        return ("` ", "")
    return ("", "")


def _select_afterglow_suffix(afterglow: float, jitter: float) -> str:
    """Map afterglow to lingering tail markers."""
    if afterglow >= 0.72:
        return " :::"
    if afterglow >= 0.5:
        return " ..."
    if jitter >= 0.78:
        return " .."
    return ""


def _select_tone_hint(wave: WaveParameter) -> str:
    """Map wave characteristics to a compact tone hint."""
    if wave.density >= 0.82:
        return " / packed"
    if wave.density <= 0.28:
        return " / spare"
    if wave.jitter >= 0.86:
        return " / fray"
    if wave.afterglow >= 0.6:
        return " / linger"
    if wave.glow >= 0.62:
        return " / bright"
    if wave.frequency >= 0.74:
        return " / quick"
    return ""


def _compress_high_end(value: float, midpoint: float, slope: float) -> float:
    """Compress values near 1.0 so high-end saturation is less common."""
    if value <= 0.0:
        return 0.0
    if value >= 1.0:
        value = 1.0
    scaled = 1.0 / (1.0 + math.exp(-(value - midpoint) / slope))
    return max(0.0, min(1.0, scaled))
