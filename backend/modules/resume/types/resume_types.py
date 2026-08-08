from dataclasses import dataclass


@dataclass
class ResumeContact:
    name: str
    portfolio_url: str
    email: str
    phone: str
    linkedin_url: str
    github_url: str
    gfg_url: str
    leetcode_url: str


@dataclass
class ResumeExperienceEntry:
    title: str
    company: str
    duration: str
    base_bullets: list[str]


@dataclass
class ResumeCertification:
    label: str
    url: str


@dataclass
class ResumeEducation:
    degree: str
    institution: str
    years: str


@dataclass
class ResumeInput:
    contact: ResumeContact
    base_summary: str
    experience: list[ResumeExperienceEntry]
    skills: list[str]
    certifications: list[ResumeCertification]
    education: list[ResumeEducation]


@dataclass
class ResumeAiOutput:
    summary: str
    experience_bullets: list[list[str]]
    skills: list[str]


@dataclass
class ResumeGenerationOutcome:
    job_id: int
    file_path: str | None = None
    reason: str | None = None
    error: str | None = None
