"""Configuration records for deterministic MAVS-GC Phase 1 infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from src.core.types import console_log, ensure_unit_interval


@dataclass(frozen=True)
class SpecialistConfig:
    accuracy: float = 0.92
    noise_amplitude: float = 0.18
    overconfidence_error_rate: float = 0.18
    fragility_threshold: float = 0.72
    adversarial_strength: float = 0.88

    def __post_init__(self) -> None:
        ensure_unit_interval(self.accuracy, "accuracy")
        ensure_unit_interval(self.noise_amplitude, "noise_amplitude")
        ensure_unit_interval(self.overconfidence_error_rate, "overconfidence_error_rate")
        ensure_unit_interval(self.fragility_threshold, "fragility_threshold")
        ensure_unit_interval(self.adversarial_strength, "adversarial_strength")


@dataclass(frozen=True)
class GovernanceConfig:
    theta_0: float = 0.0
    lambda_severity: float = 1.0
    delta_mitigation: float = 0.25
    tau_hard: float = 3.25
    w_min: float = 0.0
    w_max: float = 1.0
    diagnostic_weights: dict[str, float] = field(
        default_factory=lambda: {
            "disagreement": 1.0,
            "corruption": 1.0,
            "overconfidence": 1.0,
            "inconsistency": 1.0,
        }
    )

    def __post_init__(self) -> None:
        if self.lambda_severity < 0.0:
            raise ValueError("lambda_severity must be nonnegative")
        if self.delta_mitigation < 0.0:
            raise ValueError("delta_mitigation must be nonnegative")
        if self.tau_hard < 0.0:
            raise ValueError("tau_hard must be nonnegative")
        if self.w_min < 0.0 or self.w_max < self.w_min:
            raise ValueError("weight bounds must satisfy 0 <= w_min <= w_max")
        for name, weight in self.diagnostic_weights.items():
            if weight < 0.0:
                raise ValueError(f"diagnostic weight {name!r} must be nonnegative")


@dataclass(frozen=True)
class BenchmarkConfig:
    seed: int = 20260618
    case_count: int = 300
    specialist: SpecialistConfig = field(default_factory=SpecialistConfig)
    governance: GovernanceConfig = field(default_factory=GovernanceConfig)
    metadata: dict[str, Any] = field(default_factory=dict)
    config_id: str | None = None

    def __post_init__(self) -> None:
        if self.case_count <= 0:
            raise ValueError("case_count must be positive")
        materialized_id = self.config_id or self.compute_config_id()
        object.__setattr__(self, "config_id", materialized_id)
        # console.log: record stable configuration materialization.
        console_log("config.ready", f"configuration {materialized_id} initialized")

    @classmethod
    def default(cls) -> "BenchmarkConfig":
        # console.log: mark default configuration construction.
        console_log("config.default", "building default deterministic benchmark config")
        return cls()

    def compute_config_id(self) -> str:
        payload = repr(
            {
                "seed": self.seed,
                "case_count": self.case_count,
                "specialist": self.specialist,
                "governance": self.governance,
                "metadata": sorted(self.metadata.items()),
            }
        ).encode("utf-8")
        digest = sha256(payload).hexdigest()[:12]
        return f"cfg-{digest}"
