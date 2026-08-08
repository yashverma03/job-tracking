import json
import os

from pydantic import ValidationError

from common.exceptions.api_exceptions import ApiError
from modules.resume.types.resume_types import ResumeInput

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
        return ResumeInput.model_validate(raw)
    except ValidationError as exc:
        error_list = '\n'.join(
            f'- {".".join(str(part) for part in error["loc"])}: {error["msg"]}' for error in exc.errors()
        )
        raise ApiError(f'resume-input.json failed schema validation:\n{error_list}', status_code=500) from exc
