import { useQuery } from '@tanstack/react-query'

import { fetchJobs } from '../../../common/api/jobs/jobs.service'
import type { JobFilters } from '../interfaces/job.interfaces'

export const jobsQueryKey = (filters: JobFilters) => ['jobs', filters] as const

export function useJobsQuery(filters: JobFilters) {
  return useQuery({
    queryKey: jobsQueryKey(filters),
    queryFn: () => fetchJobs(filters),
    placeholderData: (previousData) => previousData,
  })
}
