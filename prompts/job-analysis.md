# Job Search Funnel & Platform Analysis — Prompt

Use this prompt with a job application tracker CSV (in the format described below) to get a full funnel, referral, and platform breakdown.

---

## 0. Input Data

File: a job application tracker CSV, with the following columns:
| Column | Description |
|---|---|
| `id` | Row ID |
| `url` | Job posting URL (used to derive the platform) |
| `referral_status` | One of: `Not asking`, `Referral asked`, `Referral got`, `Referral required` |
| `status` | One of: `Applied`, `To Apply`, `In Progress`, `Rejected`, `Other`, `Not considering`, `Duplicate`, `Pending` |
| `company_name` | Often blank, especially for LinkedIn Easy Apply rows |
| `title` | Job title, often blank |
| `notes` | Free-text log of everything that happened after applying (screening calls, tests, interview rounds, HR calls, assignments, offers, rejections, remarks). Empty for most rows — only populated when something beyond "applied" happened |
| `created_at` | Application date |

**Important nuance:** `status` alone is NOT a reliable signal of progress — almost everything sits at `Applied` even when real progress happened, because progress is logged only in free-text `notes`. The presence of non-empty `notes` is the real signal that something happened after the application.

---

## 1. Base Universe & Cleaning

1. Compute **Total rows** in the file.
2. Exclude rows where `status` is `Duplicate` → these are not real applications, remove entirely from all denominators.
3. Exclude rows where `status` is `To Apply` or `Pending` → these were never actually submitted, so exclude from the "applied" denominator, but report their count separately (pipeline not yet actioned).
4. **Applications Applied** = count of remaining rows where an application was actually submitted (i.e. `status` in `{Applied, In Progress, Rejected, Other, Not considering}` — basically everything except `Duplicate`, `To Apply`, `Pending`).
5. Report the count excluded at each step so the math is auditable (Total → minus Duplicate → minus To Apply/Pending → Applications Applied).

---

## 2. Referral Analysis

Using `referral_status` over the **Applications Applied** base from step 1:

- **% asked for referral** = (`Referral asked` + `Referral got`) / Applications Applied × 100
  - (i.e. any row where a referral was actively pursued, whether or not it succeeded)
- **% referral obtained** = `Referral got` / Applications Applied × 100
- **% referral required but not obtained** = `Referral required` / Applications Applied × 100
- **% not asking** = `Not asking` / Applications Applied × 100
- **Referral success rate** = `Referral got` / (`Referral asked` + `Referral got`) × 100 (of the ones actively pursued, what fraction converted)

Report as a table with counts and percentages for all four `referral_status` values.

---

## 3. Overall Progress / Response Rate

- **Any progress made** = rows where `notes` is non-empty (i.e., something happened beyond just submitting the application), OR `status` is one of `In Progress`, `Rejected`, `Other`, `Not considering` (since these statuses themselves imply an outcome was reached even without notes).
- **% got some response/progress** = Any progress made / Applications Applied × 100
- **% no response at all** (pure silence — status stuck at `Applied`, notes empty) = 100 − above

This is the single most important top-line "conversion" number: out of everything applied to, what fraction moved even one step forward (screening call, test, interview, HR reach-out, rejection communicated, etc.) versus total silence.

---

## 4. Funnel Stage Classification (parse the `notes` column)

For every row with non-empty `notes`, classify which stage(s) it reached by scanning the free text for these patterns (case-insensitive). A single row can hit multiple stages — track the **furthest/highest stage reached** per row, but also count how many rows *ever* mention each stage (some rows go straight to a later stage without an explicit HR call mention).

Define this stage ladder, from earliest to latest:

1. **HR Outreach / Screening Call** — keywords: `HR called`, `HR messaged`, `HR emailed`, `HR reached out`, `screening call`, `screening`
2. **Online Test / Assessment** — keywords: `test given`, `test link`, `assignment got`, `assignment`, `MCQs`, `AI interview` (treat "AI interview" as an automated screening test unless notes clarify it was a real interview)
3. **Interview Round(s)** — keywords: `interview round`, `interview given`, `tech interview`, `technical interview`, `LLD`, `DSA` (in interview context, not test context)
4. **Offer Stage** — keywords: `offer letter`, `offering`, `LPA` (compensation numbers mentioned), `offer`
5. **Rejected / Not Proceeding** — keywords: `not considering`, `not proceeding`, `rejected`, `did not clear`, or explicit `Rejected`/`Not considering` in `status`
6. **Self-withdrawn** — cases where the note shows *I* declined (e.g. "not doing assignment", "I rejected [the offer]") — track separately from company-side rejection, since this is a different signal (my choice vs. their rejection)

For each stage, compute:
- **Count of applications that reached at least this stage**
- **% of Applications Applied that reached at least this stage**
- **Stage-to-stage conversion %** (e.g. of those who got a screening call, what % moved to test/interview; of those who tested, what % got an interview; of those interviewed, what % got an offer)

Present this as a funnel table, e.g.:

| Stage | Count | % of Total Applied | % Converted from Previous Stage |
|---|---|---|---|
| Applied | X | 100% | — |
| HR Outreach / Screening Call | X | X% | X% |
| Test / Assignment | X | X% | X% |
| Interview Round(s) | X | X% | X% |
| Offer Received | X | X% | X% |

Also report:
- **Total offers received** (count and list, with company name if available and whether accepted, rejected by me, or still pending)
- **Total rejections** (company-side) as % of Applications Applied

---

## 5. Company-Level Callback List

Produce a list of **every company name where any callback/progress occurred** (i.e. non-empty `notes`, or `status` in `In Progress`/`Rejected`/`Other`/`Not considering`), showing:
- Company name (pull from `company_name` column; if blank, note "Not captured — LinkedIn Easy Apply" or similar, and if inferable from context in `notes`, extract it from there instead)
- Highest stage reached (per the ladder in Section 4)
- Final outcome (Offer / Rejected / Ghosted after progress / Self-withdrawn / In Progress-ongoing)

Sort this list by how far it progressed (offers first, then interviews, then tests, then screening-only).

---

## 6. Platform Breakdown

Derive the **platform** for every row from the `url` column (extract the domain), using these groupings:

| Platform Category | Domain match |
|---|---|
| LinkedIn | `linkedin.com` |
| Wellfound | `wellfound.com` |
| Hirist | `hirist.tech` |
| Instahyre | `instahyre.com` |
| Cutshort | `cutshort.io` |
| Company Career Page / ATS (direct) | everything else — e.g. `myworkdayjobs.com`, `eightfold.ai`, `greenhouse.io`, `oraclecloud.com`, individual company career domains (`careers.*`, `jobs.*`) — group these together as "Direct/Company ATS" but also break out the top individual companies by name |

For each platform category, compute:
- **Applications Applied** (count + % of total applied)
- **% asked for referral** (Section 2 logic, scoped to this platform)
- **% referral got**
- **% any progress made** (Section 3 logic, scoped to this platform)
- **% reached interview stage or beyond**
- **% offers received**
- **Best-performing platform** = the one with the highest "any progress made" or "offer" rate (call this out explicitly, and separately call out the highest-volume platform, since volume ≠ conversion)

Present as one comparison table, one row per platform, sorted by application volume, with a written 2-3 line takeaway on which platform is actually converting vs. which is just high-volume/low-yield.

---

## 7. What's Working vs. What's Not (synthesis)

Based on all of the above, write a short synthesis section covering:
- Which platform(s) yield the best conversion (screening calls / interviews / offers) relative to volume
- Whether asking for a referral correlates with better progress (compare "any progress made %" for referral-asked/got rows vs. not-asking rows)
- Common reasons for self-withdrawal or rejection, pulled from the qualitative remarks in `notes` (e.g. compensation mismatch, work-life balance concerns, tech stack mismatch, role scope mismatch)
- Any patterns in job titles/roles/companies that convert better (if enough data)
- 3-5 concrete, actionable recommendations for the next phase of the job search

---

## 8. Final Analysis, Suggestions & Summary

A closing section, separate from and more actionable than the Section 7 synthesis, that pulls everything together into something directly usable to improve job-hunting strategy going forward:
- **What's working**: the specific platforms, application patterns (e.g. referrals, role types, company types), and behaviors that are correlated with progress/offers — call out the ones worth doubling down on
- **What's not working**: platforms, patterns, or habits correlated with silence/rejection/self-withdrawal — call out the ones worth cutting back on or changing
- **Root causes**: for the biggest drop-off point in the funnel (e.g. screening→interview, or interview→offer), a short hypothesis on why, grounded in the qualitative remarks in `notes`
- **Concrete next-steps**: a prioritized list (most impactful first) of specific changes to make — e.g. which platforms to prioritize/deprioritize, whether to ask for referrals more consistently, which role types or company types to target or avoid, any resume/interview-prep gaps suggested by the remarks
- **One-paragraph summary**: a tight, plain-language wrap-up of the overall state of the job search and the single highest-leverage change to make next

---

## 9. Output Format

Present the full analysis as:
1. A short executive summary (5-6 bullet points with the headline numbers)
2. The cleaning/base-universe table (Section 1)
3. The referral table (Section 2)
4. The overall progress rate (Section 3)
5. The funnel table with stage-to-stage conversion (Section 4)
6. The company callback list (Section 5)
7. The platform comparison table (Section 6)
8. The synthesis section (Section 7)
9. The final analysis, suggestions & summary (Section 8)

Show all percentages to 1 decimal place. Show raw counts alongside every percentage (never a bare percentage with no denominator visible).
