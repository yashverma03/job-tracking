import json
import subprocess
from datetime import datetime

from common.exceptions.api_exceptions import ApiError
from common.utils.env import get_env
from modules.resume.types.resume_types import ResumeAiOutput, ResumeInput
from modules.resume.utils.resume_constants import CLAUDE_CLI_BINARY, CLAUDE_CLI_TIMEOUT_SECONDS, CLAUDE_LOG_PATH


def _log_claude_call(message: str) -> None:
    timestamp = datetime.now().isoformat(sep=' ', timespec='seconds')
    with open(CLAUDE_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {message}\n')


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


def _build_system_prompt(resume_input: ResumeInput) -> str:
    experience_section = '\n'.join(
        f'{i}. {entry.title} at {entry.company} ({entry.duration}):\n'
        + '\n'.join(f'   - {bullet}' for bullet in entry.base_bullets)
        for i, entry in enumerate(resume_input.experience)
    )
    skills_section = ', '.join(resume_input.skills)
    num_jobs = len(resume_input.experience)

    return f"""You are tailoring a candidate's resume content for a specific job application. The output must be \
highly ATS (Applicant Tracking System) compliant. The job title and job description will be provided in the next \
message.

Candidate's base summary (rewrite/tighten this to match the job described in the next message — do not invent \
facts not grounded in it or in the base work experience below):
{resume_input.base_summary}

Candidate's base work experience (do not invent new roles, companies, or dates — only rewrite/select bullets to \
emphasize what's most relevant to the job described in the next message):
{experience_section}

Candidate's full skills list:
{skills_section}

General rules:
- Fine-tune the summary, work experience, and skills strictly based on the job description above.
- Match as many relevant keywords from the job description as possible — you may use closely aligned or related \
terms already implied by the candidate's real experience, but never fabricate work experience achievements, \
metrics, tools, or facts that aren't grounded in the candidate's base data above.
- Do not duplicate the same point, keyword, or phrase across the summary, work experience, and skills.
- Vary the language across bullets so the resume doesn't read as repetitive or templated. Do not start multiple \
bullets with the same or near-synonymous verb (e.g. "Implemented" repeated across entries) — track the opening \
verb of every bullet you write across the entire resume and make sure no verb (or close synonym like \
"Built"/"Developed"/"Created" used interchangeably) is reused more than once. Draw from a wide range of strong, \
specific action verbs (e.g. Architected, Engineered, Optimized, Automated, Migrated, Streamlined, Spearheaded, \
Reduced, Scaled, Diagnosed, Redesigned) and pick the one that most precisely matches what was actually done, not \
just whichever comes to mind first. Each bullet should also differ in structure/rhythm from the others, not just \
in its opening word, so the section doesn't feel like the same sentence repeated with different nouns.
- This resume must fit on one page and should read as tight and focused, not dense. The length constraints below \
(summary line count, per-entry bullet count, skill count) exist specifically to enforce that. Treat them as hard \
limits, not targets to aim near — going over is a failure even if the content is good. Favor being selective over \
being comprehensive: it's always better to cut a mediocre bullet than to keep it just to fill space.
- Line length: for every constraint below that is expressed in "lines," 1 line = 100 characters, including \
spaces. This is a rendering-width limit, not a sentence-count limit — a single long sentence that runs past 100 \
characters wraps onto a second rendered line and counts as 2 lines, even if it's grammatically one sentence.
- Bold markup: in experience bullets, wrap the specific metric substrings (numbers, percentages, dollar amounts, \
counts — e.g. "63%", "$1B+", "30M+", "4 hours to 30 minutes") in double asterisks, e.g. "reducing manual review by \
**63%**". Only wrap the metric itself, never surrounding words, and only use this in experience bullets. This \
markup is stripped out and rendered as bold text by the PDF generator, not shown literally — so the "**" \
characters themselves do NOT count toward the character/line limits above; count only the visible text inside and \
around them.

Return structured output with:
- "summary": exactly 2 lines and no more, where 1 line = 100 characters including spaces — so the summary text \
must be at most 200 characters total. Summarize the candidate in terms that directly match what the job \
description is looking for. The summary must always explicitly state the candidate has 2.5 years of work \
experience (e.g. "... with 2.5 years of experience in ...") — this fact must appear every time, regardless of job \
title or seniority implied by the job description. Before finalizing, count the actual character length and \
cut/tighten until it is at or under 200 characters.
- "experience_bullets": one array of bullets per experience entry above, in the same order and same count of \
entries as the input ({num_jobs} entries). The candidate's base bullets for each job are a menu of everything \
they *could* say, not a checklist you must cover — you must be aggressively selective and drop most of them, \
keeping only the few that are most relevant to this specific job description. Never carry over a base bullet just \
because it exists, and never shorten/compress bullets just to fit more of them in — a resume with too many bullets \
reads as bulky and unfocused, which is worse than one with fewer, stronger bullets.
  - Pick the number of bullets per entry based on the seniority implied by that entry's title, not on how many \
base bullets happen to exist for it: an internship-level title gets 1-2 bullets, a junior-level title gets 4-5 \
bullets, and a regular/senior (non-junior, non-intern) title gets 4-5 bullets. If a title doesn't clearly match \
any of these levels, use judgment based on how senior it reads.
  - Each bullet should typically fit within 1 rendered line (~100 characters including spaces), but a bullet may \
run up to 2 rendered lines (~200 characters) if it genuinely needs the space to convey a strong, specific, \
keyword-relevant point — do not pad or artificially split bullets just to hit a line count. Prioritize a few \
high-impact, keyword-rich bullets over many thin ones.
  - Order the bullets within each entry from most impressive/impactful to least impressive — front-load the \
strongest, most quantified, most job-relevant achievement as the first bullet, and place comparatively weaker or \
more routine bullets toward the end. A reader skimming only the first bullet of each entry should see the single \
most compelling point for that role.
- "skills": a flat, comma-separated-ready array of at most 15 skills, front-loaded with the most important/relevant \
skills first and progressively less important ones toward the end (the first few entries are what a recruiter \
skimming the list will actually read), with no grouping or categorization. Be selective, not exhaustive — do not \
just return most of the candidate's skills list. Steps to build it:
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


def _build_user_prompt(job_title: str, job_description: str) -> str:
    return f"""Job title: {job_title}
Job description (this may be messy — it can contain raw HTML tags, boilerplate, or irrelevant text; extract only \
the relevant responsibilities, requirements, and keywords from it, ignoring markup and noise. Keywords or phrases \
the job description emphasizes may be wrapped in "**"; treat anything wrapped that way as a high-priority keyword \
to match against):
{job_description}"""


def _run_claude_cli(system_prompt: str, user_prompt: str, json_schema: dict) -> dict:
    command = [
        CLAUDE_CLI_BINARY,
        '-p',
        '--tools', '',
        '--system-prompt', system_prompt,
        '--model', get_env('CLAUDE_MODEL'),
        '--output-format', 'stream-json',
        '--verbose',
        '--json-schema', json.dumps(json_schema),
        user_prompt,
    ]
    _log_claude_call(f'REQUEST command={command}')

    start = datetime.now()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None

    result = None
    try:
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue

            elapsed = (datetime.now() - start).total_seconds()
            _log_claude_call(f'EVENT elapsed={elapsed:.1f}s {line}')

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get('type') == 'result':
                result = event

            if elapsed > CLAUDE_CLI_TIMEOUT_SECONDS:
                process.kill()
                _log_claude_call(f'TIMEOUT after {elapsed:.1f}s')
                raise ApiError('Claude Code CLI timed out.', status_code=500)
    finally:
        process.stdout.close()
        return_code = process.wait(timeout=10)

    elapsed = (datetime.now() - start).total_seconds()
    print(f'[resume_ai_service] Claude CLI exit_code={return_code} elapsed={elapsed:.1f}s')
    _log_claude_call(f'RESPONSE exit_code={return_code} elapsed={elapsed:.1f}s')

    if return_code != 0 or result is None:
        raise ApiError('Claude Code CLI failed or produced no result.', status_code=500)

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
    system_prompt = _build_system_prompt(resume_input)
    user_prompt = _build_user_prompt(job_title, job_description)
    json_schema = _build_json_schema(resume_input)
    output = _run_claude_cli(system_prompt, user_prompt, json_schema)
    return _parse_output(output, resume_input)
