import { useState, type FormEvent } from 'react';
import { X } from 'lucide-react';

import type { ScraperPipelineTriggerRequest } from '../interfaces/job.interfaces';
import styles from './FetchLatestJobsModal.module.css';

const DEFAULT_MAX_JOBS_PER_RUN = 1000;

interface FetchLatestJobsModalProps {
  onClose: () => void;
  onSubmit: (payload: ScraperPipelineTriggerRequest) => void;
  isSubmitting: boolean;
}

export function FetchLatestJobsModal({
  onClose,
  onSubmit,
  isSubmitting,
}: FetchLatestJobsModalProps) {
  const [maxJobsPerRun, setMaxJobsPerRun] = useState(
    String(DEFAULT_MAX_JOBS_PER_RUN),
  );
  const [startOffset, setStartOffset] = useState('0');

  const parsedMaxJobsPerRun = Number(maxJobsPerRun);
  const parsedStartOffset = Number(startOffset);
  const isValid =
    Number.isInteger(parsedMaxJobsPerRun) &&
    parsedMaxJobsPerRun >= 1 &&
    parsedMaxJobsPerRun <= 1000 &&
    Number.isInteger(parsedStartOffset) &&
    parsedStartOffset >= 0;

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!isValid) return;

    onSubmit({
      maxJobsPerRun: parsedMaxJobsPerRun,
      startOffset: parsedStartOffset,
    });
  };

  return (
    <div
      className={styles.overlay}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className={styles.modal}>
        <div className={styles.headerRow}>
          <h2 className={styles.heading}>Get Latest Jobs</h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.label}>
            Max jobs to check
            <input
              type="number"
              className={styles.input}
              value={maxJobsPerRun}
              onChange={(event) => setMaxJobsPerRun(event.target.value)}
              min={1}
              max={1000}
              disabled={isSubmitting}
              autoFocus
            />
          </label>

          <label className={styles.label}>
            Start offset
            <input
              type="number"
              className={styles.input}
              value={startOffset}
              onChange={(event) => setStartOffset(event.target.value)}
              min={0}
              disabled={isSubmitting}
            />
            <span className={styles.hint}>
              Listing index to resume pagination from (0 to start over).
            </span>
          </label>

          <div className={styles.actions}>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={isSubmitting || !isValid}
            >
              {isSubmitting ? 'Queuing...' : 'Start'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
