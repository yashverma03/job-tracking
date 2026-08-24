import type { Job } from '../types/job.types';
import profileData from '../../../../../backend/modules/resume/data/resume-input.json';

const PROFILE_NAME = profileData.contact.name;
const PROFILE_TITLE = profileData.contact.title;
const PROFILE_EMAIL = profileData.contact.email;
const PROFILE_PHONE = profileData.contact.phone;
const PROFILE_PORTFOLIO_URL = profileData.contact.portfolio_url;
const PROFILE_RESUME_URL = profileData.contact.resume_url;
const PROFILE_EXPERIENCE_SUMMARY = profileData.base_summary;
const PROFILE_SKILLS_SUMMARY = profileData.skills_summary;

const PROFILE_INTRO_SENTENCE = `I'm a ${PROFILE_TITLE}${PROFILE_EXPERIENCE_SUMMARY.slice(PROFILE_EXPERIENCE_SUMMARY.indexOf(' with '))}.`;

function assertJobsHaveRequiredFields(jobs: Job[]): void {
  requireField(jobs, (job) => Boolean(job.title), 'job title');
  requireField(jobs, (job) => Boolean(job.companyName), 'company name');
  requireField(
    jobs,
    (job) => Boolean(job.url || job.secondaryUrl || job.officialId),
    'job URL or job ID',
  );
}

function requireField(
  jobs: Job[],
  predicate: (job: Job) => boolean,
  fieldLabel: string,
): void {
  const invalidJobs = jobs.filter((job) => !predicate(job));
  if (invalidJobs.length > 0) {
    const ids = invalidJobs.map((job) => job.id).join(', ');
    throw new Error(
      `Job(s) ${ids} missing required field for message generation: ${fieldLabel}`,
    );
  }
}

function jobIdSuffix(job: Job): string {
  return job.officialId ? ` (ID: ${job.officialId})` : '';
}

function effectiveUrl(job: Job): string | null {
  return job.secondaryUrl || job.url || null;
}

function requireOfficialId(job: Job): string {
  if (!job.officialId) {
    throw new Error(
      `Job ${job.id} is missing both a URL and a job ID for message generation`,
    );
  }
  return job.officialId;
}

function formatJobsList(jobs: Job[]): string {
  const multipleJobs = jobs.length > 1;
  return jobs
    .map((job, index) => {
      const numbering = multipleJobs ? `${index + 1}. ` : '';
      const url = effectiveUrl(job);
      const titleLine = `${numbering}${job.title}${url ? jobIdSuffix(job) : ''}`;
      const locatorLine = url ?? `Job ID: ${requireOfficialId(job)}`;
      return `${titleLine}\n${locatorLine}`;
    })
    .join('\n');
}

function singleJobLine(job: Job): string {
  const url = effectiveUrl(job);
  if (url) {
    return `Job: ${url}${jobIdSuffix(job)}`;
  }
  return `Job ID: ${requireOfficialId(job)}`;
}

function sharedCompanyName(jobs: Job[]): string | null {
  const [first, ...rest] = jobs;
  const allSameCompany = rest.every(
    (job) => job.companyName === first.companyName,
  );
  return allSameCompany ? first.companyName : null;
}

const SHORT_REFERRAL_MESSAGE_MAX_LENGTH = 300;

type ShortMessageMode = 'urlAndId' | 'urlOnly' | 'idOnly';

function buildShortReferralJobsBlock(
  jobs: Job[],
  mode: ShortMessageMode,
): string {
  const [firstJob] = jobs;
  const isSingle = jobs.length === 1;

  if (mode === 'idOnly') {
    requireField(jobs, (job) => Boolean(job.officialId), 'job ID');
    return isSingle
      ? `Job ID: ${firstJob.officialId}`
      : `Job IDs: ${jobs.map((job) => job.officialId).join(', ')}`;
  }

  requireField(jobs, (job) => Boolean(effectiveUrl(job)), 'job URL');
  const includeId = mode === 'urlAndId';

  return isSingle
    ? `Job: ${effectiveUrl(firstJob)}${includeId ? jobIdSuffix(firstJob) : ''}`
    : `Jobs:\n${jobs
        .map((job) => `${effectiveUrl(job)}${includeId ? jobIdSuffix(job) : ''}`)
        .join('\n')}`;
}

function buildShortReferralMessage(jobs: Job[], mode: ShortMessageMode): string {
  const [firstJob] = jobs;

  const jobsBlock = buildShortReferralJobsBlock(jobs, mode);

  return `
Hi, I'm ${PROFILE_NAME}, ${PROFILE_TITLE}.
I'm interested in the ${firstJob.title} role at ${firstJob.companyName} and would appreciate your referral.

${jobsBlock}
Resume: ${PROFILE_RESUME_URL}

Thanks
`.trim();
}

export function getShortReferralMessage(jobs: Job[]): string {
  if (jobs.length === 0) return '';
  assertJobsHaveRequiredFields(jobs);

  const allHaveUrl = jobs.every((job) => Boolean(effectiveUrl(job)));

  if (allHaveUrl) {
    const withUrlAndId = buildShortReferralMessage(jobs, 'urlAndId');
    if (withUrlAndId.length <= SHORT_REFERRAL_MESSAGE_MAX_LENGTH) {
      return withUrlAndId;
    }

    const withUrlOnly = buildShortReferralMessage(jobs, 'urlOnly');
    if (withUrlOnly.length <= SHORT_REFERRAL_MESSAGE_MAX_LENGTH) {
      return withUrlOnly;
    }
  }

  return buildShortReferralMessage(jobs, 'idOnly');
}

export function getLongReferralMessage(jobs: Job[]): string {
  if (jobs.length === 0) return '';
  assertJobsHaveRequiredFields(jobs);

  const jobsList = formatJobsList(jobs);
  const company = sharedCompanyName(jobs) ?? 'your organisation';

  return `
Hi,

${PROFILE_INTRO_SENTENCE}

${PROFILE_SKILLS_SUMMARY}

My experience in developing reliable and efficient software applications makes me a strong fit for this role. I request your kind referral for the following role${jobs.length > 1 ? 's' : ''} at ${company}:

${jobsList}

Please find my resume attached for your reference.

Best regards,
${PROFILE_NAME}
${PROFILE_EMAIL}
${PROFILE_PHONE}
`.trim();
}

export function getEmailMessage(jobs: Job[]): string {
  if (jobs.length === 0) return '';
  assertJobsHaveRequiredFields(jobs);

  const isSingle = jobs.length === 1;
  const [firstJob] = jobs;
  const company = sharedCompanyName(jobs);

  const subject = isSingle
    ? `Application for ${firstJob.title}`
    : `Application for ${jobs.length} roles`;

  const applySentence = isSingle
    ? `I am enthusiastic about the opportunity and would like to apply for the role of ${firstJob.title} at ${firstJob.companyName}.`
    : `I am enthusiastic about these opportunities and would like to apply for the following role${jobs.length > 1 ? 's' : ''}${company ? ` at ${company}` : ''}:`;

  const jobsBlock = isSingle
    ? singleJobLine(firstJob)
    : `Jobs:\n${formatJobsList(jobs)}`;

  return `
${subject}

Hi,

${PROFILE_INTRO_SENTENCE}

${PROFILE_SKILLS_SUMMARY}

My experience in developing reliable and efficient software applications makes me a strong fit for this role. ${applySentence} Thank you for considering my application. Please find my resume attached for your reference.

Resume: ${PROFILE_RESUME_URL}
Portfolio: ${PROFILE_PORTFOLIO_URL}
${jobsBlock}

Best regards,
${PROFILE_NAME}
${PROFILE_EMAIL}
${PROFILE_PHONE}
`.trim();
}
