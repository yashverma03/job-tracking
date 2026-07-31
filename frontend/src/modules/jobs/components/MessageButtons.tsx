import { useClipboard } from '../../../common/hooks/useClipboard'
import type { Job } from '../types/job.types'
import {
  getEmailMessage,
  getReferralMessage,
  getShortReferralMessage,
} from '../utils/messageGenerator'
import styles from './MessageButtons.module.css'

interface MessageButtonsProps {
  jobs: Job[]
}

export function MessageButtons({ jobs }: MessageButtonsProps) {
  const { copy, copied } = useClipboard()

  if (jobs.length === 0) return null

  return (
    <div className={styles.container}>
      <button type="button" className={styles.button} onClick={() => copy(getShortReferralMessage(jobs))}>
        Short referral msg
      </button>
      <button type="button" className={styles.button} onClick={() => copy(getReferralMessage(jobs))}>
        Long referral msg
      </button>
      <button type="button" className={styles.button} onClick={() => copy(getEmailMessage(jobs))}>
        Email msg
      </button>
      {copied && <span className={styles.copiedText}>Copied!</span>}
    </div>
  )
}
