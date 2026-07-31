import { MessageButtons } from './MessageButtons'
import type { Job } from '../types/job.types'

interface BulkActionsBarProps {
  selectedJobs: Job[]
}

export function BulkActionsBar({ selectedJobs }: BulkActionsBarProps) {
  if (selectedJobs.length < 2) return null

  return (
    <div className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2">
      <span className="text-sm text-blue-800">{selectedJobs.length} jobs selected</span>
      <MessageButtons jobs={selectedJobs} />
    </div>
  )
}
