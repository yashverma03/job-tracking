import axios from 'axios'

import { API_BASE_URL } from '../../configs/api.config'
import type {
  JobCreateRequest,
  JobListQueryParams,
  JobListResponse,
  JobResponse,
  JobUpdateRequest,
} from '../../../modules/jobs/interfaces/job.interfaces'

const client = axios.create({ baseURL: API_BASE_URL })

export async function fetchJobs(params: JobListQueryParams): Promise<JobListResponse> {
  const { data } = await client.get<JobListResponse>('/jobs', { params })
  return data
}

export async function createJob(payload: JobCreateRequest): Promise<JobResponse> {
  const { data } = await client.post<JobResponse>('/jobs', payload)
  return data
}

export async function updateJob(id: number, payload: JobUpdateRequest): Promise<JobResponse> {
  const { data } = await client.patch<JobResponse>(`/jobs/${id}`, payload)
  return data
}

export async function deleteJob(id: number): Promise<void> {
  await client.delete(`/jobs/${id}`)
}
