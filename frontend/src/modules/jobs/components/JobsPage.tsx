import { useMemo, useState } from 'react'

import { DEFAULT_PAGE_SIZE } from '../../../common/constants/pagination.constants'
import { JobsFilters } from './JobsFilters'
import { JobsTable } from './JobsTable'
import { BulkActionsBar } from './BulkActionsBar'
import { JobFormModal } from './JobFormModal'
import { useJobMutations } from '../hooks/useJobMutations'
import { useJobsQuery } from '../hooks/useJobsQuery'
import type { JobFilters as JobFiltersState, JobFormValues } from '../interfaces/job.interfaces'
import type { Job } from '../types/job.types'

const INITIAL_FILTERS: JobFiltersState = { page: 1, limit: DEFAULT_PAGE_SIZE }

export function JobsPage() {
  const [filters, setFilters] = useState<JobFiltersState>(INITIAL_FILTERS)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [editingJob, setEditingJob] = useState<Job | null>(null)
  const [isFormOpen, setIsFormOpen] = useState(false)

  const { data, isLoading, isError } = useJobsQuery(filters)
  const { createMutation, updateMutation, deleteMutation } = useJobMutations()

  const jobs = useMemo(() => data?.items ?? [], [data])
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  const selectedJobs = useMemo(
    () => jobs.filter((job) => selectedIds.has(job.id)),
    [jobs, selectedIds],
  )

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const openAddForm = () => {
    setEditingJob(null)
    setIsFormOpen(true)
  }

  const openEditForm = (job: Job) => {
    setEditingJob(job)
    setIsFormOpen(true)
  }

  const closeForm = () => setIsFormOpen(false)

  const handleFormSubmit = (values: JobFormValues) => {
    if (editingJob) {
      updateMutation.mutate({ id: editingJob.id, payload: values })
    } else {
      createMutation.mutate(values)
    }
    closeForm()
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
    setSelectedIds((prev) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }

  const goToPage = (page: number) => setFilters((prev) => ({ ...prev, page }))

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Job Tracker</h1>
        <button
          type="button"
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          onClick={openAddForm}
        >
          Add Job
        </button>
      </div>

      <JobsFilters filters={filters} onChange={setFilters} />

      <BulkActionsBar selectedJobs={selectedJobs} />

      {isLoading && <p className="text-sm text-gray-500">Loading jobs...</p>}
      {isError && <p className="text-sm text-red-600">Failed to load jobs.</p>}

      {!isLoading && !isError && (
        <>
          <JobsTable
            jobs={jobs}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onEdit={openEditForm}
            onDelete={handleDelete}
          />

          <div className="flex items-center justify-between text-sm">
            <span>
              Page {filters.page} of {totalPages} ({data?.total ?? 0} jobs)
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                className="rounded border border-gray-300 px-3 py-1 disabled:opacity-50"
                disabled={filters.page <= 1}
                onClick={() => goToPage(filters.page - 1)}
              >
                Previous
              </button>
              <button
                type="button"
                className="rounded border border-gray-300 px-3 py-1 disabled:opacity-50"
                disabled={filters.page >= totalPages}
                onClick={() => goToPage(filters.page + 1)}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {isFormOpen && (
        <JobFormModal job={editingJob} onClose={closeForm} onSubmit={handleFormSubmit} />
      )}
    </div>
  )
}
