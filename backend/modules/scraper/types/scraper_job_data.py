from dataclasses import dataclass


@dataclass
class ScraperJobData:
    url: str
    title: str | None = None
    company_name: str | None = None
    location: str | None = None
    description: str | None = None
