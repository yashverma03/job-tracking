import type { ChangeEvent } from 'react'

import { JOB_REFERRAL_STATUS_OPTIONS, JOB_STATUS_OPTIONS } from '../constants/job.constants'
import type { JobFilters } from '../interfaces/job.interfaces'

interface JobsFiltersProps {
  filters: JobFilters
  onChange: (filters: JobFilters) => void
}

export function JobsFilters({ filters, onChange }: JobsFiltersProps) {
  const updateFilter = (patch: Partial<JobFilters>) => {
    onChange({ ...filters, ...patch, page: 1 })
  }

  const handleTextChange =
    (key: keyof JobFilters) => (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value
      updateFilter({ [key]: value || undefined })
    }

  const handleSelectChange =
    (key: keyof JobFilters) => (event: ChangeEvent<HTMLSelectElement>) => {
      const value = event.target.value
      updateFilter({ [key]: (value || undefined) as never })
    }

  return (
    <div className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-white p-4">
      <label className="flex flex-col text-sm">
        Status
        <select
          className="mt-1 rounded border border-gray-300 px-2 py-1"
          value={filters.status ?? ''}
          onChange={handleSelectChange('status')}
        >
          <option value="">All</option>
          {JOB_STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col text-sm">
        Referral status
        <select
          className="mt-1 rounded border border-gray-300 px-2 py-1"
          value={filters.referral_status ?? ''}
          onChange={handleSelectChange('referral_status')}
        >
          <option value="">All</option>
          {JOB_REFERRAL_STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col text-sm">
        From
        <input
          type="date"
          className="mt-1 rounded border border-gray-300 px-2 py-1"
          value={filters.date_from ?? ''}
          onChange={handleTextChange('date_from')}
        />
      </label>

      <label className="flex flex-col text-sm">
        To
        <input
          type="date"
          className="mt-1 rounded border border-gray-300 px-2 py-1"
          value={filters.date_to ?? ''}
          onChange={handleTextChange('date_to')}
        />
      </label>

      <label className="flex flex-1 min-w-[200px] flex-col text-sm">
        Search
        <input
          type="text"
          placeholder="URL, title, company, official ID, description"
          className="mt-1 rounded border border-gray-300 px-2 py-1"
          value={filters.search ?? ''}
          onChange={handleTextChange('search')}
        />
      </label>
    </div>
  )
}
