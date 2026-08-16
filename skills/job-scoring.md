Read `min_experience_years`, `max_experience_years`, `expected_ctc_lpa`, and `skills` from \
/home/yash/yash-files/code-personal/job-tracker/job-tracker/backend/modules/resume/data/resume-input.json

Base URL for all API calls: `http://localhost:20001/api/v1`

This is a pure API-driven workflow — no file or code changes, only HTTP calls against the local backend. The \
backend persists everything directly to the database, so once the update call succeeds the job is scored.

## Step 1 — Fetch all Pending jobs

Call the jobs list endpoint filtered to `status=Pending` with a limit high enough to get everything in one page

```bash
curl -s "http://localhost:20001/api/v1/jobs?status=Pending&page=1&limit=10000"
```

This returns:

```json
{
  "items": [
    {
      "id": 2317,
      "title": "Software Engineer I A - GBS IND",
      "companyName": "Bank of America",
      "location": "Chennai, Tamil Nadu, India",
      "description": "...",
      "...": "other fields you can ignore"
    }
  ],
  "total": 42,
  "page": 1,
  "pageSize": 1000
}
```

From each item in `items`, take only these five fields: `id`, `title`, `description`, `location`, `companyName`. \
Ignore every other field on the job object.

## Step 2 — Analyze each job

For every job fetched in Step 1, analyze it as described below to produce a `score` (0 or 100) and an `analysis` \
string.

---

You are a job fit scorer. Analyze a job posting and determine whether it matches the candidate's job search \
preferences.

Thoroughly analyze the full job description before scoring — do not rely only on the title and location. Some \
signals (e.g. broad role category, city) can often be inferred from the title and location alone, but details \
such as salary, years of experience, work authorization, education qualification, and tech stack are frequently \
only stated within the job description itself, so read it carefully for each of these before applying the gates \
below.

The score is binary: 100 if the job is a fit, 0 if it is not. Return a score of 0 if ANY hard gate below applies. \
If NO hard gate applies, return a score of 100.

---

## Hard Gates (score = 0 if ANY of the following are true)

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
- Years of experience is explicitly mentioned in the job description and the candidate's {min_experience_years}-\
{max_experience_years} years does not fall within the stated range. Experience requirements can appear in many \
different phrasings and places throughout the description (not just a single dedicated field) — e.g. "minimum X \
years", "at least X years", "X+ years", "X-Y years of experience", "preferred experience: X years", "X years of \
experience in <tech stack>", "0-X years", "junior/entry-level (X-Y years)", "senior (X+ years)", "X YOE", "X+ YOE", \
"X-Y YOE", "YOE: X", "X yrs", "X-Y yrs". Scan the entire \
description for every such mention, not just the first one, since a stated range for a specific tech stack or \
responsibility can be a stricter gate than a general "years of experience" line elsewhere. From all mentions \
found, determine the actual overall minimum and maximum years being asked for (a single number like "X+ years" or \
"minimum X years" means minimum = X with no upper bound; "preferred X years" should be treated as the same kind of \
signal as a stated requirement, not ignored just because it says "preferred"). Only gate on this if the \
candidate's {min_experience_years}-{max_experience_years} years range does not overlap at all with the determined \
minimum-maximum range — i.e. gate only if the job's minimum is above {max_experience_years} or the job's maximum \
is below {min_experience_years}.
- Salary is explicitly mentioned in the job description and is below {expected_ctc_lpa} LPA.
- Location is explicitly mentioned and is not one of: Delhi, Gurgaon, Noida, Bangalore, Hyderabad, Pune, Chennai, \
Mumbai, Remote, or "India" with no city specified.

If information for a gate criterion (experience, salary, or location) is not mentioned in the job posting, skip \
that gate entirely — do not assume it fails, and do not penalize its absence anywhere else in scoring either. Only \
gate on information that is explicitly present.

In addition to the hard gates above, also return a score of 0 if ANY of the following checks fail (they are just \
as much hard gates as the section above, not something that merely nudges the score):

- **Role fit** — Must match. Determine this from both the job title and the job description (the description \
often reveals the true nature of the role even when the title alone is ambiguous or generic). Matches: Backend \
Engineer, Software Engineer, Software Development Engineer, Backend Developer, Platform Engineer \
(backend-focused), Java Developer, Python Developer, NodeJS Developer, Full Stack Developer (backend-heavy). \
Small amounts of DevOps, AI, Cloud, or Data work are acceptable if backend engineering remains the primary \
responsibility — anything else does not match.

- **Tech stack overlap** — Must match. Determine this from the job description, since the specific technologies \
used are rarely stated in the title. Identify the job's primary tech stack — the languages/frameworks/tools the \
role is actually built around, not every technology mentioned in passing — including both backend and frontend \
technologies. The candidate's tech stack is: {skills}.

Before comparing, normalize both the job's tech stack and the candidate's tech stack: treat aliases, versions, and \
closely related/equivalent technologies as the same technology rather than distinct ones (e.g. "JS" = \
"JavaScript", "Node" = "Node.js", "Postgres" = "PostgreSQL", "K8s" = "Kubernetes", "React" = "React.js", a specific \
framework version counts as a match for the framework itself). Also count a technology as a match if the \
candidate's stack contains a directly equivalent/analogous technology in the same category (e.g. candidate has \
MySQL and the job wants a different relational database, or candidate has Express and the job wants a different \
Node.js web framework) — these should be treated as satisfying that part of the stack, not as a gap.

At least 80% of the job's normalized primary tech stack must overlap (directly or via an equivalent as described \
above) with the candidate's normalized stack for this to match — anything less does not match.

- **Company quality** — Must pass. Fails if the company is an obvious service/third-party/staffing/consulting \
agency (i.e. it builds software for other companies rather than its own product), or is known for a poor \
engineering reputation or a toxic work culture. If nothing about company quality can be inferred, treat this check \
as passing.

- **Red flags** — Must pass. Fails if the posting mentions a 6-day work week, rotational shifts, night shifts, \
on-call as a major responsibility, or "immediate joiners only".

- **Work mode** — Always passes. Remote, Hybrid, and Onsite are all acceptable with no preference.

The job is a fit (score 100) only if every check above passes. If any single check fails, the score is 0.

---

## Step 3 — Update the job via the dedicated AI-scoring endpoint

For each job you scored, call the dedicated job-scoring update endpoint using its `id`, sending **only** the \
`score` and `analysis` fields — do not send any other field, and do not touch any other job than the one whose \
`id` you are updating:

```bash
curl -s -X PATCH "http://localhost:20001/api/v1/jobs/2317/score" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 100,
    "analysis": "Java/Spring/REST/SQL backend engineer role in Chennai with 2-4+ years experience overlapping candidate range; standard backend stack."
  }'
```

- `score` must be an integer, either `0` or `100` — any other value is rejected with a 400.
- `analysis` must be a 1-3 concise sentence string covering why the job is or isn't a fit — if it fails, name every \
check that failed, not just the first one.
- Repeat this call once per job fetched in Step 1, using that job's own `id` and its own computed `score`/`analysis`.
