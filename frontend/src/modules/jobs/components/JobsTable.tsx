import { Pencil } from 'lucide-react'

import { useClipboard } from '../../../common/hooks/useClipboard'
import { MessageButtons } from './MessageButtons'
import type { Job } from '../types/job.types'
import styles from './JobsTable.module.css'

interface Column {
  key: keyof Job
  label: string
  truncate?: boolean
}

const COLUMNS: Column[] = [
  { key: 'url', label: 'URL', truncate: true },
  { key: 'referralStatus', label: 'Referral status' },
  { key: 'status', label: 'Status' },
  { key: 'companyName', label: 'Company name' },
  { key: 'title', label: 'Title' },
  { key: 'officialId', label: 'Official ID' },
  { key: 'description', label: 'Description', truncate: true },
  { key: 'location', label: 'Location' },
  { key: 'minYears', label: 'Min years' },
  { key: 'maxYears', label: 'Max years' },
]

interface JobsTableProps {
  jobs: Job[]
  selectedIds: Set<number>
  onToggleSelect: (id: number) => void
  onEdit: (job: Job) => void
}

export function JobsTable({ jobs, selectedIds, onToggleSelect, onEdit }: JobsTableProps) {
  const { copy } = useClipboard()

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead className={styles.thead}>
          <tr>
            <th className={`${styles.th} ${styles.checkboxCell}`} />
            <th className={`${styles.th} ${styles.cellWrap}`}>ID</th>
            {COLUMNS.map((column) => (
              <th
                key={column.key}
                className={`${styles.th} ${column.truncate ? styles.cellTruncate : styles.cellWrap}`}
              >
                {column.label}
              </th>
            ))}
            <th className={`${styles.th} ${styles.messagesCell}`}>Messages</th>
            <th className={`${styles.th} ${styles.actionsCell}`}>Actions</th>
          </tr>
        </thead>
        <tbody className={styles.tbody}>
          {jobs.map((job) => (
            <tr key={job.id} className={styles.row}>
              <td className={styles.checkboxCell}>
                <input
                  type="checkbox"
                  className={styles.checkbox}
                  checked={selectedIds.has(job.id)}
                  onChange={() => onToggleSelect(job.id)}
                />
              </td>
              <td className={styles.cellWrap}>{job.id}</td>
              {COLUMNS.map((column) => {
                if (column.key === 'url') {
                  return (
                    <td key={column.key} className={styles.cellTruncate}>
                      <button
                        type="button"
                        className={styles.urlButton}
                        onClick={() => copy(job.url)}
                        title="Click to copy"
                      >
                        {job.url}
                      </button>
                    </td>
                  )
                }
                return (
                  <td key={column.key} className={column.truncate ? styles.cellTruncate : styles.cellWrap}>
                    {job[column.key] ?? ''}
                  </td>
                )
              })}
              <td className={styles.messagesCell}>
                <MessageButtons jobs={[job]} />
              </td>
              <td className={styles.actionsCell}>
                <button
                  type="button"
                  className={styles.editButton}
                  onClick={() => onEdit(job)}
                  aria-label="Edit job"
                >
                  <Pencil size={16} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
