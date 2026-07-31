const NAUKRI_HOST_PREFIX = 'https://www.naukri.com'
const LINKEDIN_JOB_ID_PATTERN = /(?:currentJobId=|jobs\/view\/)(\d+)/

function stripQueryParams(url: string): string {
  const index = url.indexOf('?')
  return index !== -1 ? url.slice(0, index) : url
}

function cleanNaukriUrl(url: string): string {
  return url.startsWith(NAUKRI_HOST_PREFIX) ? stripQueryParams(url) : url
}

function extractLinkedinJobId(url: string): string | null {
  const match = url.match(LINKEDIN_JOB_ID_PATTERN)
  return match ? match[1] : null
}

function cleanLinkedinUrl(url: string): string {
  const jobId = extractLinkedinJobId(url)
  return jobId ? `https://www.linkedin.com/jobs/view/${jobId}` : url
}

export function cleanJobUrl(url: string): string {
  const trimmed = url.trim()
  if (trimmed.includes('linkedin.com')) return cleanLinkedinUrl(trimmed)
  return cleanNaukriUrl(trimmed)
}
