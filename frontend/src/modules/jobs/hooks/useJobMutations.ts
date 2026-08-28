import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';

import {
  createJob,
  deleteJob,
  generateResumeForJob,
  generateResumes,
  triggerScraperPipeline,
  updateJob,
} from '../../../common/api/jobs/jobs.service';
import { extractErrorMessage } from '../../../common/utils/error.utils';
import type {
  GenerateResumesOutcome,
  JobCreateRequest,
  JobUpdateRequest,
} from '../interfaces/job.interfaces';

interface UpdateMutationArgs {
  id: number;
  payload: JobUpdateRequest;
}

interface BulkUpdateMutationArgs {
  ids: number[];
  payload: JobUpdateRequest;
}

function extractResumeOutcomeError(error: unknown): string | undefined {
  if (!axios.isAxiosError(error)) return undefined;
  const data = error.response?.data as GenerateResumesOutcome | undefined;
  return data?.error ?? extractErrorMessage(error);
}

export function useJobMutations() {
  const queryClient = useQueryClient();
  const invalidateJobs = () =>
    queryClient.invalidateQueries({ queryKey: ['jobs'] });

  const createMutation = useMutation({
    mutationFn: (payload: JobCreateRequest) => createJob(payload),
    onSuccess: () => {
      invalidateJobs();
      toast.success('Job added');
    },
    onError: (error) =>
      toast.error(extractErrorMessage(error) ?? 'Failed to add job'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: UpdateMutationArgs) => updateJob(id, payload),
    onSuccess: () => {
      invalidateJobs();
      toast.success('Job updated');
    },
    onError: (error) =>
      toast.error(extractErrorMessage(error) ?? 'Failed to update job'),
  });

  const bulkUpdateMutation = useMutation({
    mutationFn: ({ ids, payload }: BulkUpdateMutationArgs) =>
      Promise.all(ids.map((id) => updateJob(id, payload))),
    onSuccess: () => {
      invalidateJobs();
      toast.success('Jobs updated');
    },
    onError: (error) =>
      toast.error(extractErrorMessage(error) ?? 'Failed to update jobs'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteJob(id),
    onSuccess: () => {
      invalidateJobs();
      toast.success('Job deleted');
    },
    onError: (error) =>
      toast.error(extractErrorMessage(error) ?? 'Failed to delete job'),
  });

  const generateResumesMutation = useMutation({
    mutationFn: () => generateResumes(),
    onSuccess: (result) => {
      if (result.queued) {
        toast.success(result.message);
      } else {
        toast(result.message);
      }
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error) ?? 'Failed to queue resume generation');
    },
  });

  const fetchLatestJobsMutation = useMutation({
    mutationFn: () => triggerScraperPipeline(),
    onSuccess: (result) => {
      if (result.queued) {
        toast.success(result.message);
      } else {
        toast(result.message);
      }
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error) ?? 'Failed to queue scraper run');
    },
  });

  const buildResumeMutation = useMutation({
    mutationFn: (jobId: number) => generateResumeForJob(jobId),
    onSuccess: () => {
      invalidateJobs();
      toast.success('Resume built');
    },
    onError: (error) => {
      toast.error(
        `Failed to build resume: ${extractResumeOutcomeError(error) ?? 'unknown error'}`,
      );
    },
  });

  return {
    createMutation,
    updateMutation,
    bulkUpdateMutation,
    deleteMutation,
    generateResumesMutation,
    buildResumeMutation,
    fetchLatestJobsMutation,
  };
}
