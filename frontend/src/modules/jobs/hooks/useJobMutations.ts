import { useMutation, useQueryClient } from '@tanstack/react-query'

import { createJob, deleteJob, updateJob } from '../../../common/api/jobs/jobs.service'
import type { JobCreatePayload, JobUpdatePayload } from '../types/job.types'

export function useJobMutations() {
  const queryClient = useQueryClient()
  const invalidateJobs = () => queryClient.invalidateQueries({ queryKey: ['jobs'] })

  const createMutation = useMutation({
    mutationFn: (payload: JobCreatePayload) => createJob(payload),
    onSuccess: invalidateJobs,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: JobUpdatePayload }) =>
      updateJob(id, payload),
    onSuccess: invalidateJobs,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteJob(id),
    onSuccess: invalidateJobs,
  })

  return { createMutation, updateMutation, deleteMutation }
}
