import json
import subprocess

from common.exceptions.api_exceptions import ApiError
from modules.resume.types.resume_types import ResumeAiOutput, ResumeInput
from modules.resume.utils.resume_constants import (
    CLAUDE_CLI_BINARY,
    CLAUDE_CLI_TIMEOUT_SECONDS,
    MAX_BULLET_CHARS,
    MAX_SKILL_ITEM_CHARS,
    MAX_SKILLS_PER_CATEGORY,
    MAX_SUMMARY_CHARS,
)


def _build_json_schema(resume_input: ResumeInput) -> dict:
    return {
        'type': 'object',
        'properties': {
            'summary': {'type': 'string'},
            'experience_bullets': {
                'type': 'array',
                'items': {'type': 'array', 'items': {'type': 'string'}},
                'minItems': len(resume_input.experience),
                'maxItems': len(resume_input.experience),
            },
            'skills': {
                'type': 'object',
                'properties': {
                    category: {'type': 'array', 'items': {'type': 'string'}}
                    for category in resume_input.skills_pool
                },
                'required': list(resume_input.skills_pool.keys()),
            },
        },
        'required': ['summary', 'experience_bullets', 'skills'],
    }


def _build_prompt(job_title: str, job_description: str, resume_input: ResumeInput) -> str:
    experience_section = '\n'.join(
        f'{i}. {entry.title} at {entry.company} ({entry.duration}):\n'
        + '\n'.join(f'   - {bullet}' for bullet in entry.base_bullets)
        for i, entry in enumerate(resume_input.experience)
    )
    skills_section = '\n'.join(
        f'{category}: {", ".join(items)}' for category, items in resume_input.skills_pool.items()
    )

    return f"""You are tailoring a candidate's resume content for a specific job application.

Job title: {job_title}
Job description:
{job_description}

Candidate's base work experience (do not invent new roles, companies, or dates — only rewrite bullets to \
emphasize what's most relevant to the job above):
{experience_section}

Candidate's full skills pool (choose and order the most relevant subset per category, do not invent skills \
not listed here):
{skills_section}

Return structured output with:
- "summary": a resume summary tailored to this job, at most {MAX_SUMMARY_CHARS} characters.
- "experience_bullets": one array of bullets per experience entry above, in the same order, same count of \
entries as the input, each bullet at most {MAX_BULLET_CHARS} characters and rewritten/reordered to best fit \
the job (do not fabricate facts, only rephrase/reprioritize the given base bullets).
- "skills": an object with the same category keys as the skills pool above, each containing at most \
{MAX_SKILLS_PER_CATEGORY} of the most relevant items (in relevance order) from that category's pool, each \
item at most {MAX_SKILL_ITEM_CHARS} characters."""


def _run_claude_cli(prompt: str, json_schema: dict) -> dict:
    try:
        completed = subprocess.run(
            [
                CLAUDE_CLI_BINARY,
                '-p',
                '--tools', '',
                '--output-format', 'json',
                '--json-schema', json.dumps(json_schema),
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=CLAUDE_CLI_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ApiError('Claude Code CLI not found on PATH.', status_code=500) from exc
    except subprocess.TimeoutExpired as exc:
        raise ApiError('Claude Code CLI timed out.', status_code=500) from exc

    if completed.returncode != 0:
        raise ApiError(f'Claude Code CLI failed: {completed.stderr.strip()}', status_code=500)

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ApiError('Claude Code CLI returned malformed JSON.', status_code=500) from exc

    if result.get('is_error') or 'structured_output' not in result:
        raise ApiError(f'Claude Code CLI returned an error result: {result.get("result")}', status_code=500)

    return result['structured_output']


def _enforce_limits(output: dict, resume_input: ResumeInput) -> ResumeAiOutput:
    summary = str(output['summary'])[:MAX_SUMMARY_CHARS]

    raw_bullets = output['experience_bullets']
    if len(raw_bullets) != len(resume_input.experience):
        raise ApiError('AI response experience_bullets count does not match resume input experience count.',
                        status_code=500)
    experience_bullets = [
        [str(bullet)[:MAX_BULLET_CHARS] for bullet in bullets]
        for bullets in raw_bullets
    ]

    raw_skills = output['skills']
    skills = {
        category: [str(item)[:MAX_SKILL_ITEM_CHARS] for item in raw_skills.get(category, [])][:MAX_SKILLS_PER_CATEGORY]
        for category in resume_input.skills_pool
    }

    return ResumeAiOutput(summary=summary, experience_bullets=experience_bullets, skills=skills)


def generate_resume_content(job_title: str, job_description: str, resume_input: ResumeInput) -> ResumeAiOutput:
    prompt = _build_prompt(job_title, job_description, resume_input)
    json_schema = _build_json_schema(resume_input)
    output = _run_claude_cli(prompt, json_schema)
    return _enforce_limits(output, resume_input)
