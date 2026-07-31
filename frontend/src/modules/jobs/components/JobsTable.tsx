import { MessageButtons } from './MessageButtons'
import type { Job } from '../types/job.types'

interface Column {
  key: keyof Job
  label: string
}

const COLUMNS: Column[] = [
  { key: 'id', label: 'ID' },
  { key: 'url', label: 'URL' },
  { key: 'referral_status', label: 'Referral Status' },
  { key: 'status', label: 'Status' },
  { key: 'company_name', label: 'Company Name' },
  { key: 'title', label: 'Title' },
  { key: 'official_id', label: 'Official ID' },
  { key: 'description', label: 'Description' },
  { key: 'location', label: 'Location' },
  { key: 'min_years', label: 'Min Years' },
  { key: 'max_years', label: 'Max Years' },
  { key: 'notes', label: 'Notes' },
  { key: 'created_at', label: 'Created At' },
  { key: 'updated_at', label: 'Updated At' },
]

interface JobsTableProps {
  jobs: Job[]
  selectedIds: Set<number>
  onToggleSelect: (id: number) => void
  onEdit: (job: Job) => void
  onDelete: (id: number) => void
}

export function JobsTable({ jobs, selectedIds, onToggleSelect, onEdit, onDelete }: JobsTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="p-2" />
            {COLUMNS.map((column) => (
              <th key={column.key} className="whitespace-nowrap p-2 text-left font-medium text-gray-600">
                {column.label}
              </th>
            ))}
            <th className="p-2 text-left font-medium text-gray-600">Messages</th>
            <th className="p-2 text-left font-medium text-gray-600">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {jobs.map((job) => (
            <tr key={job.id}>
              <td className="p-2">
                <input
                  type="checkbox"
                  checked={selectedIds.has(job.id)}
                  onChange={() => onToggleSelect(job.id)}
                />
              </td>
              {COLUMNS.map((column) => (
                <td key={column.key} className="max-w-xs truncate p-2">
                  {job[column.key] ?? ''}
                </td>
              ))}
              <td className="p-2">
                <MessageButtons jobs={[job]} />
              </td>
              <td className="whitespace-nowrap p-2">
                <button
                  type="button"
                  className="mr-2 text-blue-600 hover:underline"
                  onClick={() => onEdit(job)}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className="text-red-600 hover:underline"
                  onClick={() => onDelete(job.id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
