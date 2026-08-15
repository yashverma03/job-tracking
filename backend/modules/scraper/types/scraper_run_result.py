from dataclasses import dataclass, field


@dataclass
class ScraperRunResult:
    metadata: dict
    errors: list[dict] = field(default_factory=list)
