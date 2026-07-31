import type { ChangeEvent } from 'react'

import { JOB_REFERRAL_STATUS_OPTIONS, JOB_STATUS_OPTIONS } from '../constants/job.constants'
import type { JobListQueryParams } from '../interfaces/job.interfaces'
import styles from './JobsFilters.module.css'

interface JobsFiltersProps {
  filters: JobListQueryParams
  onChange: (filters: JobListQueryParams) => void
}

export function JobsFilters({ filters, onChange }: JobsFiltersProps) {
  const updateFilter = (patch: Partial<JobListQueryParams>) => {
    onChange({ ...filters, ...patch, page: 1 })
  }

  const handleTextChange =
    (key: keyof JobListQueryParams) => (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value
      updateFilter({ [key]: value || undefined })
    }

  const handleStatusChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value
    updateFilter({ status: value ? (value as JobListQueryParams['status']) : undefined })
  }

  const handleReferralStatusChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value
    updateFilter({
      referralStatus: value ? (value as JobListQueryParams['referralStatus']) : undefined,
    })
  }

  return (
    <div className={styles.container}>
      <label className={styles.field}>
        Status
        <select className={styles.input} value={filters.status ?? ''} onChange={handleStatusChange}>
          <option value="">All</option>
          {JOB_STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        Referral status
        <select
          className={styles.input}
          value={filters.referralStatus ?? ''}
          onChange={handleReferralStatusChange}
        >
          <option value="">All</option>
          {JOB_REFERRAL_STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        From
        <input
          type="date"
          className={styles.input}
          value={filters.dateFrom ?? ''}
          onChange={handleTextChange('dateFrom')}
        />
      </label>

      <label className={styles.field}>
        To
        <input
          type="date"
          className={styles.input}
          value={filters.dateTo ?? ''}
          onChange={handleTextChange('dateTo')}
        />
      </label>

      <label className={styles.searchField}>
        Search
        <input
          type="text"
          placeholder="URL, title, company, official ID, description"
          className={styles.input}
          value={filters.search ?? ''}
          onChange={handleTextChange('search')}
        />
      </label>
    </div>
  )
}
