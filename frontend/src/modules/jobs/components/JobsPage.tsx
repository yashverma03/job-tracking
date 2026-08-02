import { useMemo, useState } from 'react'

import { DEFAULT_PAGE_SIZE } from '../../../common/constants/pagination.constants'
import { JobsFilters } from './JobsFilters'
import { JobsTable } from './JobsTable'
import { BulkActionsBar } from './BulkActionsBar'
import { JobFormModal } from './JobFormModal'
import { useJobMutations } from '../hooks/useJobMutations'
import { useJobsQuery } from '../hooks/useJobsQuery'
import type { JobListQueryParams, JobUpdateRequest } from '../interfaces/job.interfaces'
import type { Job } from '../types/job.types'
import styles from './JobsPage.module.css'

const INITIAL_FILTERS: JobListQueryParams = { page: 1, limit: DEFAULT_PAGE_SIZE }

export function JobsPage() {
  const [filters, setFilters] = useState<JobListQueryParams>(INITIAL_FILTERS)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [editingJob, setEditingJob] = useState<Job | null>(null)
  const [isFormOpen, setIsFormOpen] = useState(false)

  const { data, isLoading, isError } = useJobsQuery(filters)
  const { createMutation, updateMutation, deleteMutation, generateResumesMutation, buildResumeMutation } =
    useJobMutations()

  const jobs = useMemo(() => data?.items ?? [], [data])
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.pageSize)) : 1

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

  const handleDelete = (job: Job) => {
    deleteMutation.mutate(job.id, { onSuccess: closeForm })
  }

  const handleGenerateResume = (job: Job) => {
    buildResumeMutation.mutate(job.id, {
      onSuccess: (outcome) => {
        if (!outcome.error) {
          setEditingJob((prev) =>
            prev && prev.id === job.id ? { ...prev, isCustomResumeGenerated: true } : prev,
          )
        }
      },
    })
  }

  const handleFormSubmit = (payload: JobUpdateRequest) => {
    if (editingJob) {
      updateMutation.mutate({ id: editingJob.id, payload }, { onSuccess: closeForm })
    } else {
      createMutation.mutate(payload, { onSuccess: closeForm })
    }
  }

  const goToPage = (page: number) => {
    setFilters((prev) => ({ ...prev, page }))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Job Tracker</h1>
        <button type="button" className={styles.addButton} onClick={openAddForm}>
          <span className={styles.addButtonIcon} aria-hidden="true">
            +
          </span>
          Add Job
        </button>
      </div>

      <div className={styles.toolbar}>
        <button
          type="button"
          className={styles.generateResumesButton}
          disabled={generateResumesMutation.isPending}
          onClick={() => generateResumesMutation.mutate()}
        >
          {generateResumesMutation.isPending ? 'Generating...' : 'Generate Custom Resumes'}
        </button>
      </div>

      <JobsFilters filters={filters} onChange={setFilters} />

      <BulkActionsBar selectedJobs={selectedJobs} />

      {isLoading && <p className={styles.statusText}>Loading jobs...</p>}
      {isError && <p className={styles.errorText}>Failed to load jobs.</p>}

      {!isLoading && !isError && (
        <>
          <JobsTable
            jobs={jobs}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onEdit={openEditForm}
            onDelete={handleDelete}
          />

          <div className={styles.pagination}>
            <span>
              Page {filters.page} of {totalPages} ({data?.total ?? 0} jobs)
            </span>
            <div className={styles.paginationButtons}>
              <button
                type="button"
                className={styles.pageButton}
                disabled={filters.page <= 1}
                onClick={() => goToPage(filters.page - 1)}
              >
                Previous
              </button>
              <button
                type="button"
                className={styles.pageButton}
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
        <JobFormModal
          job={editingJob}
          onClose={closeForm}
          onSubmit={handleFormSubmit}
          onDelete={handleDelete}
          onGenerateResume={handleGenerateResume}
          isGeneratingResume={buildResumeMutation.isPending}
        />
      )}
    </div>
  )
}
