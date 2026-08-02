import json
import os

from common.exceptions.api_exceptions import ApiError
from modules.resume.types.resume_types import (
    ResumeCertification,
    ResumeContact,
    ResumeEducation,
    ResumeExperienceEntry,
    ResumeInput,
)

RESUME_INPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'resume-input.json')


def load_resume_input() -> ResumeInput:
    if not os.path.exists(RESUME_INPUT_PATH):
        raise ApiError(
            'resume-input.json is missing. Copy resume-input.example.json to resume-input.json and fill it in.',
            status_code=500,
        )

    with open(RESUME_INPUT_PATH, encoding='utf-8') as f:
        try:
            raw = json.load(f)
        except json.JSONDecodeError as exc:
            raise ApiError(f'resume-input.json is not valid JSON: {exc}', status_code=500) from exc

    try:
        return ResumeInput(
            contact=ResumeContact(**raw['contact']),
            experience=[ResumeExperienceEntry(**entry) for entry in raw['experience']],
            skills=raw['skills'],
            certifications=[ResumeCertification(**cert) for cert in raw['certifications']],
            education=[ResumeEducation(**edu) for edu in raw['education']],
        )
    except (KeyError, TypeError) as exc:
        raise ApiError(f'resume-input.json is missing a required field: {exc}', status_code=500) from exc
