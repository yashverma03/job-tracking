const LINKEDIN_JOB_ID_PATTERN = /(?:currentJobId=|jobs\/view\/)(\d+)/

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
  return trimmed
}
