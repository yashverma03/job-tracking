import type { JobReferralStatus, JobStatus } from '../types/job.types'

export interface JobFilters {
  status?: JobStatus
  referral_status?: JobReferralStatus
  date_from?: string
  date_to?: string
  search?: string
  page: number
  limit: number
}

export interface JobFormValues {
  url: string
  company_name: string
  title: string
  official_id: string
  description: string
  status: JobStatus
  referral_status: JobReferralStatus
}
