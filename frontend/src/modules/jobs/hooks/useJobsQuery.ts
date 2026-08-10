import { useQuery } from '@tanstack/react-query';

import { fetchJobs } from '../../../common/api/jobs/jobs.service';
import type { JobListQueryParams } from '../interfaces/job.interfaces';

export const jobsQueryKey = (params: JobListQueryParams) =>
  ['jobs', params] as const;

export function useJobsQuery(params: JobListQueryParams) {
  return useQuery({
    queryKey: jobsQueryKey(params),
    queryFn: () => fetchJobs(params),
    placeholderData: (previousData) => previousData,
  });
}
