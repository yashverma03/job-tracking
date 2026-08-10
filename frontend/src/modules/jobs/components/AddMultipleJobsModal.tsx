import { useRef, useState, type KeyboardEvent, type UIEvent } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { X } from 'lucide-react';
import toast from 'react-hot-toast';

import { createJob } from '../../../common/api/jobs/jobs.service';
import { extractErrorMessage } from '../../../common/utils/error.utils';
import { cleanJobUrl } from '../utils/urlCleaner';
import styles from './AddMultipleJobsModal.module.css';

interface AddMultipleJobsModalProps {
  onClose: () => void;
}

interface SubmitSummary {
  successCount: number;
  failedCount: number;
  failures: Array<{ url: string; message: string }>;
}

export function AddMultipleJobsModal({ onClose }: AddMultipleJobsModalProps) {
  const queryClient = useQueryClient();
  const [text, setText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [summary, setSummary] = useState<SubmitSummary | null>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  const lineCount = text.length === 0 ? 1 : text.split('\n').length;

  const handleTextareaScroll = (event: UIEvent<HTMLTextAreaElement>) => {
    if (lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = event.currentTarget.scrollTop;
    }
  };

  const handleTextareaKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      if (!isSubmitting && text.trim() !== '') handleSave();
    }
  };

  const handleSave = async () => {
    const urls = Array.from(
      new Set(
        text
          .split('\n')
          .map((line) => cleanJobUrl(line.trim()))
          .filter((url): url is string => Boolean(url)),
      ),
    );

    if (urls.length === 0) return;

    setIsSubmitting(true);
    setSummary(null);

    const failures: Array<{ url: string; message: string }> = [];
    let successCount = 0;

    for (const url of urls) {
      try {
        await createJob({ url });
        successCount += 1;
      } catch (error) {
        failures.push({
          url,
          message: extractErrorMessage(error) ?? 'Failed to add job',
        });
      }
    }

    setIsSubmitting(false);
    setText(failures.map((failure) => failure.url).join('\n'));
    setSummary({ successCount, failedCount: failures.length, failures });

    if (successCount > 0) {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      toast.success(`Added ${successCount} job(s)`);
    }

    if (failures.length > 0) {
      toast.error(`Failed to add ${failures.length} job(s)`);
    } else {
      onClose();
    }
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
          <h2 className={styles.heading}>Add Multiple Jobs</h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <div className={styles.textareaWrapper}>
          <div ref={lineNumbersRef} className={styles.lineNumbers}>
            {Array.from({ length: lineCount }, (_, index) => (
              <div key={index}>{index + 1}</div>
            ))}
          </div>
          <textarea
            className={styles.textarea}
            value={text}
            onChange={(event) => setText(event.target.value)}
            onScroll={handleTextareaScroll}
            onKeyDown={handleTextareaKeyDown}
            spellCheck={false}
            autoFocus
          />
        </div>

        {summary && (
          <div className={styles.summary}>
            <p>
              {summary.successCount} succeeded, {summary.failedCount} failed
            </p>
            {summary.failures.length > 0 && (
              <ul className={styles.summaryFailedList}>
                {summary.failures.map((failure) => (
                  <li key={failure.url}>
                    {failure.url} — {failure.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.cancelButton}
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className={styles.submitButton}
            onClick={handleSave}
            disabled={isSubmitting || text.trim() === ''}
          >
            {isSubmitting ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
