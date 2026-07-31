import { MessageButtons } from './MessageButtons'
import type { Job } from '../types/job.types'
import styles from './BulkActionsBar.module.css'

interface BulkActionsBarProps {
  selectedJobs: Job[]
}

export function BulkActionsBar({ selectedJobs }: BulkActionsBarProps) {
  if (selectedJobs.length < 2) return null

  return (
    <div className={styles.container}>
      <span className={styles.count}>{selectedJobs.length} jobs selected</span>
      <MessageButtons jobs={selectedJobs} />
    </div>
  )
}
