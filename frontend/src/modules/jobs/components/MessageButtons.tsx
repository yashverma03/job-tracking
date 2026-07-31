import { useClipboard } from '../../../common/hooks/useClipboard'
import type { Job } from '../types/job.types'
import {
  getEmailMessage,
  getReferralMessage,
  getShortReferralMessage,
} from '../utils/messageGenerator'

interface MessageButtonsProps {
  jobs: Job[]
}

const BUTTON_CLASS =
  'rounded border border-gray-300 bg-white px-2 py-1 text-xs hover:bg-gray-50'

export function MessageButtons({ jobs }: MessageButtonsProps) {
  const { copy, copied } = useClipboard()

  if (jobs.length === 0) return null

  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className={BUTTON_CLASS}
        onClick={() => copy(getShortReferralMessage(jobs))}
      >
        Short referral msg
      </button>
      <button
        type="button"
        className={BUTTON_CLASS}
        onClick={() => copy(getReferralMessage(jobs))}
      >
        Long referral msg
      </button>
      <button
        type="button"
        className={BUTTON_CLASS}
        onClick={() => copy(getEmailMessage(jobs))}
      >
        Email msg
      </button>
      {copied && <span className="text-xs text-green-600">Copied!</span>}
    </div>
  )
}
