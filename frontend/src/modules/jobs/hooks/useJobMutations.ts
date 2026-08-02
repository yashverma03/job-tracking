import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'

import { createJob, deleteJob, generateResumes, updateJob } from '../../../common/api/jobs/jobs.service'
import type { JobCreateRequest, JobUpdateRequest } from '../interfaces/job.interfaces'

interface UpdateMutationArgs {
  id: number
  payload: JobUpdateRequest
}

function extractErrorMessage(error: unknown): string | undefined {
  if (!axios.isAxiosError(error)) return undefined
  const data = error.response?.data
  return data && typeof data === 'object' && typeof data.message === 'string'
    ? data.message
    : undefined
}

export function useJobMutations() {
  const queryClient = useQueryClient()
  const invalidateJobs = () => queryClient.invalidateQueries({ queryKey: ['jobs'] })

  const createMutation = useMutation({
    mutationFn: (payload: JobCreateRequest) => createJob(payload),
    onSuccess: () => {
      invalidateJobs()
      toast.success('Job added')
    },
    onError: (error) => toast.error(extractErrorMessage(error) ?? 'Failed to add job'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: UpdateMutationArgs) => updateJob(id, payload),
    onSuccess: () => {
      invalidateJobs()
      toast.success('Job updated')
    },
    onError: () => toast.error('Failed to update job'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteJob(id),
    onSuccess: () => {
      invalidateJobs()
      toast.success('Job deleted')
    },
    onError: () => toast.error('Failed to delete job'),
  })

  const generateResumesMutation = useMutation({
    mutationFn: () => generateResumes(),
    onSuccess: (result) => {
      invalidateJobs()
      if (result.failed.length > 0) {
        toast.error(`Generated ${result.generated.length}, failed ${result.failed.length}`)
      } else {
        toast.success(`Generated ${result.generated.length} resume(s)`)
      }
    },
    onError: () => toast.error('Failed to generate resumes'),
  })

  return { createMutation, updateMutation, deleteMutation, generateResumesMutation }
}
