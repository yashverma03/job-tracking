import { useQuery } from '@tanstack/react-query';

import { fetchJobStats } from '../../../common/api/jobs/jobs.service';

export const jobStatsQueryKey = ['jobs', 'stats'] as const;

export function useJobStatsQuery() {
  return useQuery({
    queryKey: jobStatsQueryKey,
    queryFn: fetchJobStats,
    placeholderData: (previousData) => previousData,
  });
}
