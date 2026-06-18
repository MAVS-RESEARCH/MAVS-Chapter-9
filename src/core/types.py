"""Core MAVS-GC Phase 1 data structures.

The types in this module encode the bounded score/support contract required by
the formal MAVS-GC definition while leaving governance fields optional until
Phase 2 implements diagnostics, mitigation, thresholds, consensus, and decision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any

SCORE_MIN = 0.0
SCORE_MAX = 1.0
SUPPORT_MIN = -1.0
SUPPORT_MAX = 1.0


def console_log(step: str, comment: str) -> None:
    """Emit a concise console log for auditable benchmark execution."""
    print(f"[MAVS-GC] {step}: {comment}")


def ensure_finite(value: float, field_name: str) -> float:
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite, got {value!r}")
    return value


def ensure_unit_interval(value: float, field_name: str) -> float:
    value = ensure_finite(float(value), field_name)
    if value < SCORE_MIN or value > SCORE_MAX:
        raise ValueError(f"{field_name} must be in [0, 1], got {value!r}")
    return value


def clamp_unit_interval(value: float) -> float:
    value = ensure_finite(float(value), "value")
    return max(SCORE_MIN, min(SCORE_MAX, value))


def score_to_support(score: float) -> float:
    bounded_score = ensure_unit_interval(score, "score")
    support = 2.0 * bounded_score - 1.0
    if support < SUPPORT_MIN or support > SUPPORT_MAX:
        raise ValueError(f"support must be in [-1, 1], got {support!r}")
    return support


def stable_hash_int(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int(sha256(payload).hexdigest()[:16], 16)


@dataclass(frozen=True)
class ConfigReference:
    config_id: str
    seed: int
    source: str = "phase_1"

    def __post_init__(self) -> None:
        if not self.config_id:
            raise ValueError("config_id must be nonempty")


@dataclass(frozen=True)
class SyntheticCase:
    case_id: str
    truth: int
    corruption: float
    disagreement_regime: str
    mitigation_level: float
    edge_condition: str
    features: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id must be nonempty")
        if self.truth not in (0, 1):
            raise ValueError(f"truth must be 0 or 1, got {self.truth!r}")
        ensure_unit_interval(self.corruption, "corruption")
        ensure_unit_interval(self.mitigation_level, "mitigation_level")
        for name, value in self.features.items():
            ensure_finite(float(value), f"features[{name}]")


@dataclass(frozen=True)
class SpecialistOutput:
    specialist_name: str
    score: float
    support: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_score(
        cls,
        specialist_name: str,
        score: float,
        metadata: dict[str, Any] | None = None,
    ) -> "SpecialistOutput":
        bounded_score = ensure_unit_interval(score, f"{specialist_name}.score")
        return cls(
            specialist_name=specialist_name,
            score=bounded_score,
            support=score_to_support(bounded_score),
            metadata=metadata or {},
        )

    def __post_init__(self) -> None:
        if not self.specialist_name:
            raise ValueError("specialist_name must be nonempty")
        ensure_unit_interval(self.score, f"{self.specialist_name}.score")
        ensure_finite(self.support, f"{self.specialist_name}.support")
        if self.support < SUPPORT_MIN or self.support > SUPPORT_MAX:
            raise ValueError(
                f"{self.specialist_name}.support must be in [-1, 1], got {self.support!r}"
            )


@dataclass(frozen=True)
class DecisionRecord:
    accepted: bool | None
    reason: str = "phase_1_not_evaluated"


@dataclass(frozen=True)
class MetricsInput:
    truth: int
    decision: bool | None
    score: float | None = None

    def __post_init__(self) -> None:
        if self.truth not in (0, 1):
            raise ValueError(f"truth must be 0 or 1, got {self.truth!r}")
        if self.score is not None:
            ensure_unit_interval(self.score, "score")


@dataclass(frozen=True)
class Trace:
    trace_id: str
    config: ConfigReference
    case: SyntheticCase
    specialist_scores: dict[str, float]
    supports: dict[str, float]
    diagnostics: dict[str, float] = field(default_factory=dict)
    severity: float | None = None
    weights: dict[str, float] = field(default_factory=dict)
    mitigation: float | None = None
    threshold: float | None = None
    consensus: float | None = None
    decision: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.trace_id:
            raise ValueError("trace_id must be nonempty")
        if set(self.specialist_scores) != set(self.supports):
            raise ValueError("specialist_scores and supports must have matching specialists")
        for name, score in self.specialist_scores.items():
            ensure_unit_interval(score, f"specialist_scores[{name}]")
        for name, support in self.supports.items():
            ensure_finite(support, f"supports[{name}]")
            if support < SUPPORT_MIN or support > SUPPORT_MAX:
                raise ValueError(f"supports[{name}] must be in [-1, 1], got {support!r}")
        for name, diagnostic in self.diagnostics.items():
            ensure_finite(diagnostic, f"diagnostics[{name}]")
            if diagnostic < 0.0:
                raise ValueError(f"diagnostics[{name}] must be nonnegative")
        if self.severity is not None and self.severity < 0.0:
            raise ValueError("severity must be nonnegative when provided")
        if self.mitigation is not None:
            ensure_unit_interval(self.mitigation, "mitigation")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
