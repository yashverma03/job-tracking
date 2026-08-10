import { MessageButtons } from './MessageButtons';
import type { Job } from '../types/job.types';
import styles from './BulkActionsBar.module.css';

interface BulkActionsBarProps {
  selectedJobs: Job[];
}

export function BulkActionsBar({ selectedJobs }: BulkActionsBarProps) {
  const isVisible = selectedJobs.length >= 2;

  return (
    <div
      className={styles.container}
      style={{ visibility: isVisible ? 'visible' : 'hidden' }}
    >
      <span className={styles.count}>{selectedJobs.length} jobs selected</span>
      <div className={styles.actions}>
        <MessageButtons jobs={isVisible ? selectedJobs : []} />
      </div>
    </div>
  );
}
