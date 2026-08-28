from dataclasses import dataclass, field


@dataclass
class ScraperJobData:
    """A single candidate job as it flows through the pipeline: built from a listing
    page (possibly with some fields still missing), then enriched in place with
    whatever the detail page adds. `extra` is a scraper-private bag for identifiers
    needed only to fetch that scraper's detail page (e.g. a numeric position id) -
    the base class never reads it."""

    url: str
    title: str | None = None
    company_name: str | None = None
    location: str | None = None
    description: str | None = None
    official_id: str | None = None
    extra: dict = field(default_factory=dict)
