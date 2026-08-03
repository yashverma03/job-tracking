import { useQuery } from '@tanstack/react-query'

import { fetchCompanyNames, fetchJobTitles } from '../../../common/api/jobs/jobs.service'

export const SUGGESTIONS_LIMIT = 10

export function useCompanyNamesQuery(search: string) {
  return useQuery({
    queryKey: ['jobs', 'company-names', search, SUGGESTIONS_LIMIT],
    queryFn: () => fetchCompanyNames(search, SUGGESTIONS_LIMIT),
    staleTime: 60_000,
    placeholderData: (previousData) => previousData,
  })
}

export function useJobTitlesQuery(search: string) {
  return useQuery({
    queryKey: ['jobs', 'job-titles', search, SUGGESTIONS_LIMIT],
    queryFn: () => fetchJobTitles(search, SUGGESTIONS_LIMIT),
    staleTime: 60_000,
    placeholderData: (previousData) => previousData,
  })
}
