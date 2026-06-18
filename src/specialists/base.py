"""Specialist protocol and all-speak evaluation helpers."""

from __future__ import annotations

from typing import Protocol, Sequence

from src.core.types import SpecialistOutput, SyntheticCase, console_log


class Specialist(Protocol):
    name: str

    def predict(self, case: SyntheticCase) -> float:
        """Return a calibrated synthetic score in [0, 1]."""


def evaluate_all(specialists: Sequence[Specialist], case: SyntheticCase) -> list[SpecialistOutput]:
    if not specialists:
        raise ValueError("at least one specialist is required")
    names = [specialist.name for specialist in specialists]
    if len(set(names)) != len(names):
        raise ValueError("specialist names must be unique")
    # console.log: record all-speak evaluation start.
    console_log("specialists.evaluate_all", f"evaluating {len(specialists)} specialists")
    outputs: list[SpecialistOutput] = []
    for specialist in specialists:
        score = specialist.predict(case)
        outputs.append(
            SpecialistOutput.from_score(
                specialist_name=specialist.name,
                score=score,
                metadata={"case_id": case.case_id},
            )
        )
        # console.log: record each specialist score after bounded conversion.
        console_log("specialists.output", f"{specialist.name} produced bounded score")
    return outputs

