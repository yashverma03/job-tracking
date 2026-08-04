import toast from 'react-hot-toast';

import { useClipboard } from '../../../common/hooks/useClipboard';
import type { Job } from '../types/job.types';
import {
  getEmailMessage,
  getLongReferralMessage,
  getShortReferralMessage,
} from '../utils/messageGenerator';
import styles from './MessageButtons.module.css';

interface MessageButtonsProps {
  jobs: Job[];
}

export function MessageButtons({ jobs }: MessageButtonsProps) {
  const { copy } = useClipboard();

  const copyMessage = (generateMessage: (jobs: Job[]) => string) => {
    try {
      copy(generateMessage(jobs));
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to generate message',
      );
    }
  };

  return (
    <div className={styles.container}>
      <button
        type="button"
        className={styles.button}
        onClick={() => copyMessage(getShortReferralMessage)}
      >
        Short
      </button>
      <button
        type="button"
        className={styles.button}
        onClick={() => copyMessage(getLongReferralMessage)}
      >
        Long
      </button>
      <button
        type="button"
        className={styles.button}
        onClick={() => copyMessage(getEmailMessage)}
      >
        Email
      </button>
    </div>
  );
}
