import { useMutation, useQueryClient } from '@tanstack/react-query'

import { createJob, deleteJob, updateJob } from '../../../common/api/jobs/jobs.service'
import type { JobCreateRequest, JobUpdateRequest } from '../interfaces/job.interfaces'

interface UpdateMutationArgs {
  id: number
  payload: JobUpdateRequest
}

export function useJobMutations() {
  const queryClient = useQueryClient()
  const invalidateJobs = () => queryClient.invalidateQueries({ queryKey: ['jobs'] })

  const createMutation = useMutation({
    mutationFn: (payload: JobCreateRequest) => createJob(payload),
    onSuccess: invalidateJobs,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: UpdateMutationArgs) =>
      updateJob(id, payload),
    onSuccess: invalidateJobs,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteJob(id),
    onSuccess: invalidateJobs,
  })

  return { createMutation, updateMutation, deleteMutation }
}
