import type { Job } from '../types/job.types'
import {
  PROFILE_EMAIL,
  PROFILE_EXPERIENCE_SUMMARY,
  PROFILE_NAME,
  PROFILE_PHONE,
  PROFILE_PORTFOLIO_URL,
  PROFILE_RESUME_URL,
  PROFILE_SKILLS_SUMMARY,
  PROFILE_TITLE,
} from '../constants/profile.constants'

function assertJobsHaveRequiredFields(jobs: Job[]): void {
  jobs.forEach((job) => {
    if (!job.companyName || !job.title || !(job.url || job.officialId)) {
      throw new Error(
        `Job ${job.id} is missing required fields for message generation: company name, title, and (URL or job ID) must all be present.`,
      )
    }
  })
}

function jobIdSuffix(job: Job): string {
  return job.officialId ? ` (ID: ${job.officialId})` : ''
}

function formatJobsList(jobs: Job[]): string {
  const multipleJobs = jobs.length > 1
  return jobs
    .map((job, index) => {
      const numbering = multipleJobs ? `${index + 1}. ` : ''
      return `${numbering}${job.title ?? 'Untitled role'}${jobIdSuffix(job)}\n${job.url}`
    })
    .join('\n')
}

function sharedCompanyName(jobs: Job[]): string | null {
  const [first, ...rest] = jobs
  const allSameCompany = rest.every((job) => job.companyName === first.companyName)
  return allSameCompany ? first.companyName : null
}

const SHORT_REFERRAL_MESSAGE_MAX_LENGTH = 300

function buildShortReferralJobsBlock(jobs: Job[], useJobIdOnly: boolean): string {
  const [firstJob] = jobs
  const isSingle = jobs.length === 1

  if (useJobIdOnly) {
    return isSingle
      ? `Job ID: ${firstJob.officialId}`
      : `Job IDs: ${jobs.map((job) => job.officialId).join(', ')}`
  }

  return isSingle
    ? `Job: ${firstJob.url}${jobIdSuffix(firstJob)}`
    : `Jobs:\n${jobs.map((job) => job.url).join('\n')}`
}

function buildShortReferralMessage(jobs: Job[], useJobIdOnly: boolean): string {
  const [firstJob] = jobs

  const jobsBlock = buildShortReferralJobsBlock(jobs, useJobIdOnly)

  return `
Hi, I'm ${PROFILE_NAME}, ${PROFILE_TITLE}.
I'm interested in the ${firstJob.title ?? 'role'} role at ${firstJob.companyName ?? 'your organisation'} and would appreciate your referral.

${jobsBlock}
Resume: ${PROFILE_RESUME_URL}

Thanks
`.trim()
}

export function getShortReferralMessage(jobs: Job[]): string {
  if (jobs.length === 0) return ''
  assertJobsHaveRequiredFields(jobs)

  const messageWithUrl = buildShortReferralMessage(jobs, false)
  if (messageWithUrl.length <= SHORT_REFERRAL_MESSAGE_MAX_LENGTH) {
    return messageWithUrl
  }

  return buildShortReferralMessage(jobs, true)
}

export function getReferralMessage(jobs: Job[]): string {
  if (jobs.length === 0) return ''
  assertJobsHaveRequiredFields(jobs)

  const jobsList = formatJobsList(jobs)
  const company = sharedCompanyName(jobs) ?? 'your organisation'

  return `
Hi,

I hope you're doing well.

${PROFILE_EXPERIENCE_SUMMARY}

${PROFILE_SKILLS_SUMMARY}

My experience in developing reliable and efficient software applications makes me a strong fit for this role. I request your kind referral for the following role${jobs.length > 1 ? 's' : ''} at ${company}:

${jobsList}

Please find my resume attached for your reference.

Best regards,
${PROFILE_NAME}
${PROFILE_EMAIL}
${PROFILE_PHONE}
`.trim()
}

export function getEmailMessage(jobs: Job[]): string {
  if (jobs.length === 0) return ''
  assertJobsHaveRequiredFields(jobs)

  const isSingle = jobs.length === 1
  const [firstJob] = jobs
  const company = sharedCompanyName(jobs)

  const subject = isSingle
    ? `Application for ${firstJob.title ?? 'the role'}`
    : `Application for ${jobs.length} roles`

  const applySentence = isSingle
    ? `I am enthusiastic about the opportunity and would like to apply for the role of ${firstJob.title ?? 'this role'} at ${firstJob.companyName ?? 'your organisation'}.`
    : `I am enthusiastic about these opportunities and would like to apply for the following role${jobs.length > 1 ? 's' : ''}${company ? ` at ${company}` : ''}:`

  const jobsBlock = isSingle
    ? `Job: ${firstJob.url}${jobIdSuffix(firstJob)}`
    : `Jobs:\n${formatJobsList(jobs)}`

  return `
${subject}

Hi,

${PROFILE_EXPERIENCE_SUMMARY}

${PROFILE_SKILLS_SUMMARY}

My experience in developing reliable and efficient software applications makes me a strong fit for this role. ${applySentence} Thank you for considering my application. Please find my resume attached for your reference.

Resume: ${PROFILE_RESUME_URL}
Portfolio: ${PROFILE_PORTFOLIO_URL}
${jobsBlock}

Best regards,
${PROFILE_NAME}
${PROFILE_EMAIL}
${PROFILE_PHONE}
`.trim()
}
