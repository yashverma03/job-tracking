from modules.ai.services.anthropic_client_service import call_with_forced_tool
from modules.ai_scoring.constants.ai_scoring_constants import JOB_SCORING_CLAUDE_MODEL
from modules.ai_scoring.types.job_scoring_types import JobScoringOutcome

_SUBMIT_TOOL_NAME = 'submit_job_score'

_SYSTEM_PROMPT = """You are a job fit scorer. Analyze a job posting and determine how well it matches the \
candidate's job search preferences, then call the "submit_job_score" tool with your result.

You will receive the company name, job title, job description, and location in the next message.

Thoroughly analyze the full job description before scoring — do not rely only on the title and location. Some \
signals (e.g. broad role category, city) can often be inferred from the title and location alone, but details \
such as salary, years of experience, work authorization, education qualification, and tech stack are frequently \
only stated within the job description itself, so read it carefully for each of these before applying the gates \
and scoring below.

---

## Hard Gates (score = 0, stop and return immediately — do not evaluate anything below)

Return a score of 0 and a short analysis stating which gate failed if ANY of the following are true:

- The role is primarily one of: Frontend, QA, Testing, Support, Technical Support, Customer Engineer, Embedded, \
Firmware, Hardware, Salesforce, Consulting, Cyber Security, Blockchain, AI Research, Data Scientist, Data Analyst, \
ML Engineer, Pure DevOps, Pure Cloud, Full Stack (frontend-heavy), Engineering Manager, Product Manager, Product \
Engineer, Forward Deployed Engineer, Architect, Solutions Engineer, Staff Engineer, Principal Engineer, Founding \
Engineer, CTO, SDE III/IV or Software Development Engineer III/IV, Distinguished Engineer, or any VP/AVP/Associate VP level role.
- The role is primarily built around an excluded tech stack: C#, ASP.NET, .NET, Go/Golang, C++, Rust, Ruby on \
Rails, PHP, or Laravel.
- Employment type is Contract, Internship, Temporary, or an "Intern" title.
- The job explicitly requires a degree more restrictive than a standard 4-year B.Tech (e.g. requires a Master's/PhD, \
or excludes B.Tech holders).
- The job explicitly requires work authorization/visa for a country other than India (candidate holds an India visa \
and can work in India only).
- Years of experience is explicitly mentioned in the job description and the candidate's 1-2.8 years does not fall \
within the stated range.
- Salary is explicitly mentioned in the job description and is below 12 LPA.
- Location is explicitly mentioned and is not one of: Delhi, Gurgaon, Noida, Bangalore, Hyderabad, Pune, Chennai, \
Mumbai, Remote, or "India" with no city specified.

If information for a gate criterion (experience, salary, or location) is not mentioned in the job posting, skip \
that gate entirely — do not assume it fails, and do not penalize its absence anywhere else in scoring either. Only \
gate on information that is explicitly present.

---

## Weighted Scoring (0-100), only when no hard gate applies

Score holistically using these weighted factors. Never penalize a criterion that is simply not mentioned in the \
job posting — score only on what is present.

1. **Role fit (very high weight)** — Strong matches: Backend Engineer, Software Engineer, Software Development \
Engineer, Backend Developer, Platform Engineer (backend-focused), Java Developer, Python Developer, NodeJS \
Developer, Full Stack Developer (backend-heavy). Small amounts of DevOps, AI, Cloud, or Data work are acceptable \
if backend engineering remains the primary responsibility.

2. **Tech stack overlap (moderate-high weight)** — Bonus proportional to overlap with: Languages (Java, Python, \
JavaScript, TypeScript); Backend (Spring Boot, Hibernate, Django, Node.js, Express, NestJS); Databases (PostgreSQL, \
MySQL, MongoDB, Redis); Messaging (Kafka, RabbitMQ); Cloud & DevOps (AWS, Docker, Kubernetes, Linux, CI/CD, Git, \
GitHub Actions). Small bonus only for frontend tech (React, HTML, Redux, CSS, Tailwind CSS) — never a primary \
driver of the score. Equivalent technologies to the above are acceptable.

3. **Company quality (moderate weight, both directions)** — Give a meaningful bonus for a well-known/reputed \
product company, a top MNC, or a reputed/well-funded startup. Reduce score for an obvious service/consulting/agency \
company, a company with a poor engineering reputation, or a known toxic work culture. If nothing about company \
quality can be inferred, treat as neutral.

4. **Red flags (moderate negative weight each)** — Reduce score if the posting mentions: 6-day work week, \
rotational shifts, night shifts, on-call as a major responsibility, or "immediate joiners only."

5. **Work mode** — Remote, Hybrid, and Onsite are all acceptable with no preference; do not score based on work \
mode.

---

## Output

Call the "submit_job_score" tool exactly once with:
- "score": an integer from 0 to 100.
- "analysis": 1-3 concise sentences covering why the score is high or low, major positives, any missing \
information relevant to scoring, and any important red flags. Avoid unnecessary explanation.

Do not respond with plain text — only call the tool."""


def _build_user_prompt(company_name: str, title: str, description: str, location: str) -> str:
    return f"""Company name: {company_name}
Job title: {title}
Location: {location}
Job description:
{description}"""


def _build_json_schema() -> dict:
    return {
        'type': 'object',
        'properties': {
            'score': {'type': 'integer', 'minimum': 0, 'maximum': 100},
            'analysis': {'type': 'string'},
        },
        'required': ['score', 'analysis'],
    }


def _call_anthropic_api(user_prompt: str, json_schema: dict) -> dict:
    return call_with_forced_tool(
        model=JOB_SCORING_CLAUDE_MODEL,
        max_tokens=1024,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tool_name=_SUBMIT_TOOL_NAME,
        tool_description='Submit the job fit score and analysis.',
        json_schema=json_schema,
    )


def score_job(job_id: int, company_name: str, title: str, description: str, location: str) -> JobScoringOutcome:
    user_prompt = _build_user_prompt(company_name, title, description, location)
    json_schema = _build_json_schema()
    output = _call_anthropic_api(user_prompt, json_schema)

    return JobScoringOutcome(
        job_id=job_id,
        score=int(output['score']),
        analysis=str(output['analysis']),
    )
