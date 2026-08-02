import json
import subprocess

from common.exceptions.api_exceptions import ApiError
from common.utils.env import get_env
from modules.resume.types.resume_types import ResumeAiOutput, ResumeInput
from modules.resume.utils.resume_constants import CLAUDE_CLI_BINARY, CLAUDE_CLI_TIMEOUT_SECONDS


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
                'type': 'array',
                'items': {'type': 'string'},
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
    skills_section = ', '.join(resume_input.skills)
    num_jobs = len(resume_input.experience)

    return f"""You are tailoring a candidate's resume content for a specific job application. The output must be \
highly ATS (Applicant Tracking System) compliant.

Job title: {job_title}
Job description (this may be messy — it can contain raw HTML tags, boilerplate, or irrelevant text; extract only \
the relevant responsibilities, requirements, and keywords from it, ignoring markup and noise. Keywords or phrases \
the job description emphasizes may be wrapped in "**"; treat anything wrapped that way as a high-priority keyword \
to match against):
{job_description}

Candidate's base work experience (do not invent new roles, companies, or dates — only rewrite/select bullets to \
emphasize what's most relevant to the job above):
{experience_section}

Candidate's full skills list (choose and order the most relevant subset, do not invent skills not listed here):
{skills_section}

General rules:
- Fine-tune the summary, work experience, and skills strictly based on the job description above.
- Match as many relevant keywords from the job description as possible — you may use closely aligned or related \
terms already implied by the candidate's real experience, but never invent skills, tools, or achievements that \
aren't grounded in the candidate's base data above.
- Do not duplicate the same point, keyword, or phrase across the summary, work experience, and skills.

Return structured output with:
- "summary": exactly 2 lines, summarizing the candidate in terms that directly match what the job description is \
looking for.
- "experience_bullets": one array of bullets per experience entry above, in the same order and same count of \
entries as the input ({num_jobs} entries). Across all entries combined, use a total of exactly 21 bullet lines. \
Every entry must have at least 1 bullet, and the most recent (first) entry should get proportionally more bullets \
than older entries. Pick the bullets/points from each job's base bullets that best incorporate the job \
description's keywords, rewriting/reprioritizing them for maximum keyword match, and never fabricate facts not \
present in the base bullets.
- "skills": a flat, comma-separated-ready array of the skills from the candidate's skills list that match the job \
description, ordered by relevance; remove any skills from the list that are irrelevant to this job, with no \
grouping or categorization."""


def _run_claude_cli(prompt: str, json_schema: dict) -> dict:
    try:
        completed = subprocess.run(
            [
                CLAUDE_CLI_BINARY,
                '-p',
                '--tools', '',
                '--model', get_env('CLAUDE_MODEL'),
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

    print(f'[resume_ai_service] Claude CLI response:\n{completed.stdout}')

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ApiError('Claude Code CLI returned malformed JSON.', status_code=500) from exc

    if result.get('is_error') or 'structured_output' not in result:
        raise ApiError(f'Claude Code CLI returned an error result: {result.get("result")}', status_code=500)

    return result['structured_output']


def _parse_output(output: dict, resume_input: ResumeInput) -> ResumeAiOutput:
    summary = str(output['summary'])

    raw_bullets = output['experience_bullets']
    if len(raw_bullets) != len(resume_input.experience):
        raise ApiError('AI response experience_bullets count does not match resume input experience count.',
                        status_code=500)
    experience_bullets = [[str(bullet) for bullet in bullets] for bullets in raw_bullets]

    skills = [str(item) for item in output['skills']]

    return ResumeAiOutput(summary=summary, experience_bullets=experience_bullets, skills=skills)


def generate_resume_content(job_title: str, job_description: str, resume_input: ResumeInput) -> ResumeAiOutput:
    prompt = _build_prompt(job_title, job_description, resume_input)
    json_schema = _build_json_schema(resume_input)
    output = _run_claude_cli(prompt, json_schema)
    return _parse_output(output, resume_input)
