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

Candidate's full skills list:
{skills_section}

General rules:
- Fine-tune the summary, work experience, and skills strictly based on the job description above.
- Match as many relevant keywords from the job description as possible — you may use closely aligned or related \
terms already implied by the candidate's real experience, but never fabricate work experience achievements, \
metrics, tools, or facts that aren't grounded in the candidate's base data above.
- Do not duplicate the same point, keyword, or phrase across the summary, work experience, and skills.
- This resume must fit on one page. The length constraints below (summary line count, total bullet count, skill \
count) exist specifically to enforce that. Treat them as hard limits, not targets to aim near — going over is a \
failure even if the content is good.
- Line length: for every constraint below that is expressed in "lines," 1 line = 100 characters, including \
spaces. This is a rendering-width limit, not a sentence-count limit — a single long sentence that runs past 100 \
characters wraps onto a second rendered line and counts as 2 lines, even if it's grammatically one sentence.

Return structured output with:
- "summary": exactly 2 lines and no more, where 1 line = 100 characters including spaces — so the summary text \
must be at most 200 characters total. Summarize the candidate in terms that directly match what the job \
description is looking for. Before finalizing, count the actual character length and cut/tighten until it is at \
or under 200 characters.
- "experience_bullets": one array of bullets per experience entry above, in the same order and same count of \
entries as the input ({num_jobs} entries). Across all entries combined, use a total of exactly 21 bullet lines — \
not 21 as an upper bound, exactly 21 — where each individual bullet must be written to fit within 1 rendered line \
(at most ~100 characters including spaces); if a bullet's content genuinely needs more space, it counts as \
multiple lines toward the total, so prefer tightening the wording to fit 1 line instead. Every entry must have at \
least 1 bullet, and the most recent (first) entry should get proportionally more bullets than older entries. You \
must be selective: from each job's base bullets, choose only the subset most relevant to this specific job \
description and drop the rest — do not carry over every base bullet just because it exists. Rewrite/reprioritize \
the chosen bullets to maximize keyword match with the job description, but never fabricate facts not present in \
the base bullets. Before finalizing, count the total bullet lines (accounting for any bullet that wraps past 100 \
characters as more than 1 line) across all entries and adjust until the total is exactly 21.
- "skills": a flat, comma-separated-ready array of at most 15 skills, ordered by relevance, with no grouping or \
categorization. Be selective, not exhaustive — do not just return most of the candidate's skills list. Steps to \
build it:
  1. From the candidate's skills list above, select only the skills that are actually relevant to this job \
description. Drop everything else, even if it's a fine general skill — irrelevant skills waste space.
  2. Identify important skills/technologies/tools named in the job description (including anything wrapped in \
"**") that are NOT in the candidate's skills list, but are close enough to something the candidate's real \
experience (from the work experience section above) already demonstrates that listing them is honest — e.g. the \
JD says a specific framework/library the candidate's bullets show equivalent hands-on work with. Add a small \
number of these (typically 1-4), phrased using the job description's own terminology. Do not add a skill that has \
no grounding at all in the candidate's base data.
  3. The combined list from steps 1-2 must not exceed 15 entries; if it would, keep only the highest-relevance \
ones."""


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
