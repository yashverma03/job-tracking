from dataclasses import dataclass
from datetime import date
from typing import Optional, Sequence


@dataclass
class JobFilterParams:
    page: int
    limit: int
    status: Optional[Sequence[str]] = None
    referral_status: Optional[Sequence[str]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search: Optional[str] = None
    is_custom_resume_generated: Optional[bool] = None
    has_description: Optional[bool] = None
