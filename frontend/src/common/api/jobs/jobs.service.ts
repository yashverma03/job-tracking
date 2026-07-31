import axios from 'axios'

import { API_BASE_URL } from '../../configs/api.config'
import type { PaginatedResponse } from '../../types/api.types'
import type { JobFilters } from '../../../modules/jobs/interfaces/job.interfaces'
import type { Job, JobCreatePayload, JobUpdatePayload } from '../../../modules/jobs/types/job.types'

const client = axios.create({ baseURL: API_BASE_URL })

export async function fetchJobs(filters: JobFilters): Promise<PaginatedResponse<Job>> {
  const { data } = await client.get<PaginatedResponse<Job>>('/jobs', { params: filters })
  return data
}

export async function createJob(payload: JobCreatePayload): Promise<Job> {
  const { data } = await client.post<Job>('/jobs', payload)
  return data
}

export async function updateJob(id: number, payload: JobUpdatePayload): Promise<Job> {
  const { data } = await client.patch<Job>(`/jobs/${id}`, payload)
  return data
}

export async function deleteJob(id: number): Promise<void> {
  await client.delete(`/jobs/${id}`)
}
