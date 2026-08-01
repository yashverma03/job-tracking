import type { PaginatedResponse } from '../../../common/types/api.types'
import type { Job, JobReferralStatus, JobStatus } from '../types/job.types'

export type JobResponse = Job

export type JobListResponse = PaginatedResponse<JobResponse>

export interface JobCreateRequest {
  url?: string
  secondaryUrl?: string
  companyName?: string
  title?: string
  officialId?: string
  description?: string
  location?: string
  notes?: string
  status?: JobStatus
  referralStatus?: JobReferralStatus
}

export type JobUpdateRequest = Partial<JobCreateRequest>

export interface JobListQueryParams {
  status?: JobStatus
  referralStatus?: JobReferralStatus
  dateFrom?: string
  dateTo?: string
  search?: string
  page: number
  limit: number
}

export interface JobFormValues {
  url: string
  secondaryUrl: string
  companyName: string
  title: string
  officialId: string
  description: string
  location: string
  notes: string
  status: JobStatus
  referralStatus: JobReferralStatus
}
