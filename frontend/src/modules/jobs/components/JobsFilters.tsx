import dayjs from 'dayjs';
import type { ChangeEvent } from 'react';

import { Dropdown } from '../../../common/components/Dropdown';
import {
  JOB_REFERRAL_STATUS_OPTIONS,
  JOB_STATUS_OPTIONS,
} from '../constants/job.constants';
import type { JobListQueryParams } from '../interfaces/job.interfaces';
import styles from './JobsFilters.module.css';

interface JobsFiltersProps {
  filters: JobListQueryParams;
  onChange: (filters: JobListQueryParams) => void;
}

const formatDisplayDate = (value?: string) => {
  if (!value) return '';
  return dayjs(value).format('DD MMM YYYY');
};

const STATUS_OPTIONS = JOB_STATUS_OPTIONS.map((option) => ({
  value: option,
  label: option,
}));
const REFERRAL_STATUS_OPTIONS = JOB_REFERRAL_STATUS_OPTIONS.map((option) => ({
  value: option,
  label: option,
}));

export function JobsFilters({ filters, onChange }: JobsFiltersProps) {
  const updateFilter = (patch: Partial<JobListQueryParams>) => {
    onChange({ ...filters, ...patch, page: 1 });
  };

  const handleTextChange =
    (key: keyof JobListQueryParams) =>
    (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      updateFilter({ [key]: value || undefined });
    };

  const handleStatusChange = (value: string) => {
    updateFilter({
      status: value ? (value as JobListQueryParams['status']) : undefined,
    });
  };

  const handleReferralStatusChange = (value: string) => {
    updateFilter({
      referralStatus: value
        ? (value as JobListQueryParams['referralStatus'])
        : undefined,
    });
  };

  return (
    <div className={styles.container}>
      <Dropdown
        label="Status"
        value={filters.status ?? ''}
        onChange={handleStatusChange}
        options={STATUS_OPTIONS}
        allowEmpty
      />

      <Dropdown
        label="Referral status"
        value={filters.referralStatus ?? ''}
        onChange={handleReferralStatusChange}
        options={REFERRAL_STATUS_OPTIONS}
        allowEmpty
      />

      <label className={styles.searchField}>
        <span className={styles.label}>Search</span>
        <div className={styles.searchInputWrapper}>
          <input
            type="text"
            className={styles.input}
            value={filters.search ?? ''}
            onChange={handleTextChange('search')}
          />
          {filters.search && (
            <button
              type="button"
              className={styles.clearButton}
              aria-label="Clear search"
              onClick={() => updateFilter({ search: undefined })}
            >
              ×
            </button>
          )}
        </div>
      </label>

      <label className={styles.field}>
        <span className={styles.label}>From</span>
        <div className={`${styles.input} ${styles.dateWrapper}`}>
          <input
            type="date"
            className={styles.dateInput}
            value={filters.dateFrom ?? ''}
            onChange={handleTextChange('dateFrom')}
          />
          <span className={styles.dateDisplay}>
            {formatDisplayDate(filters.dateFrom)}
          </span>
        </div>
      </label>

      <label className={styles.field}>
        <span className={styles.label}>To</span>
        <div className={`${styles.input} ${styles.dateWrapper}`}>
          <input
            type="date"
            className={styles.dateInput}
            value={filters.dateTo ?? ''}
            onChange={handleTextChange('dateTo')}
          />
          <span className={styles.dateDisplay}>
            {formatDisplayDate(filters.dateTo)}
          </span>
        </div>
      </label>
    </div>
  );
}
