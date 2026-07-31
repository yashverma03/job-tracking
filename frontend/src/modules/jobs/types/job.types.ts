import type { JOB_REFERRAL_STATUS_OPTIONS, JOB_STATUS_OPTIONS } from '../constants/job.constants'

export type JobStatus = (typeof JOB_STATUS_OPTIONS)[number]
export type JobReferralStatus = (typeof JOB_REFERRAL_STATUS_OPTIONS)[number]

export interface Job {
  id: number
  url: string
  referral_status: JobReferralStatus
  status: JobStatus
  company_name: string | null
  title: string | null
  official_id: string | null
  description: string | null
  location: string | null
  min_years: number | null
  max_years: number | null
  notes: string | null
  created_at: string
  updated_at: string
}

export type JobCreatePayload = Partial<Omit<Job, 'id' | 'created_at' | 'updated_at'>> &
  Pick<Job, 'url'>

export type JobUpdatePayload = Partial<Omit<Job, 'id' | 'created_at' | 'updated_at'>>
