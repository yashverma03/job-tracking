import type { JOB_REFERRAL_STATUS_OPTIONS, JOB_STATUS_OPTIONS } from '../constants/job.constants'

export type JobStatus = (typeof JOB_STATUS_OPTIONS)[number]
export type JobReferralStatus = (typeof JOB_REFERRAL_STATUS_OPTIONS)[number]

export interface Job {
  id: number
  url: string
  referralStatus: JobReferralStatus
  status: JobStatus
  companyName: string | null
  title: string | null
  officialId: string | null
  description: string | null
  location: string | null
  minYears: number | null
  maxYears: number | null
  notes: string | null
  createdAt: string
  updatedAt: string
}
