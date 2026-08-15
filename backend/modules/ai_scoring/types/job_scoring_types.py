from dataclasses import dataclass


@dataclass
class JobScoringOutcome:
    job_id: int
    score: int | None = None
    analysis: str | None = None
    error: str | None = None
