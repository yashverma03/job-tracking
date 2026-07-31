import dayjs from 'dayjs'

import { MessageButtons } from './MessageButtons'
import type { Job } from '../types/job.types'
import styles from './JobsTable.module.css'

const CREATED_AT_FORMAT = 'DD MMM YYYY'

interface Column {
  key: keyof Job
  label: string
}

const COLUMNS: Column[] = [
  { key: 'url', label: 'URL' },
  { key: 'referralStatus', label: 'Referral Status' },
  { key: 'status', label: 'Status' },
  { key: 'companyName', label: 'Company Name' },
  { key: 'title', label: 'Title' },
  { key: 'officialId', label: 'Official ID' },
  { key: 'description', label: 'Description' },
  { key: 'location', label: 'Location' },
  { key: 'minYears', label: 'Min Years' },
  { key: 'maxYears', label: 'Max Years' },
  { key: 'notes', label: 'Notes' },
]

interface JobsTableProps {
  jobs: Job[]
  selectedIds: Set<number>
  onToggleSelect: (id: number) => void
  onEdit: (job: Job) => void
}

export function JobsTable({ jobs, selectedIds, onToggleSelect, onEdit }: JobsTableProps) {
  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead className={styles.thead}>
          <tr>
            <th className={styles.th} />
            <th className={styles.th}>ID</th>
            <th className={styles.th}>Created At</th>
            {COLUMNS.map((column) => (
              <th key={column.key} className={styles.th}>
                {column.label}
              </th>
            ))}
            <th className={styles.th}>Messages</th>
            <th className={styles.th}>Actions</th>
          </tr>
        </thead>
        <tbody className={styles.tbody}>
          {jobs.map((job) => (
            <tr key={job.id} className={styles.row}>
              <td className={styles.td}>
                <input
                  type="checkbox"
                  checked={selectedIds.has(job.id)}
                  onChange={() => onToggleSelect(job.id)}
                />
              </td>
              <td className={styles.cellText}>{job.id}</td>
              <td className={styles.cellText}>{dayjs(job.createdAt).format(CREATED_AT_FORMAT)}</td>
              {COLUMNS.map((column) => (
                <td key={column.key} className={styles.cellText}>
                  {job[column.key] ?? ''}
                </td>
              ))}
              <td className={styles.td}>
                <MessageButtons jobs={[job]} />
              </td>
              <td className={styles.actionsCell}>
                <button type="button" className={styles.editButton} onClick={() => onEdit(job)}>
                  Edit
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
