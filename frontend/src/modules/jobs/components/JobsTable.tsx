import { CheckCheck, Pencil } from 'lucide-react';

import { Dropdown } from '../../../common/components/Dropdown';
import { useClipboard } from '../../../common/hooks/useClipboard';
import {
  REFERRAL_STATUS_DROPDOWN_OPTIONS,
  STATUS_DROPDOWN_OPTIONS,
} from '../constants/job.constants';
import { useJobMutations } from '../hooks/useJobMutations';
import { MessageButtons } from './MessageButtons';
import type { Job } from '../types/job.types';
import styles from './JobsTable.module.css';

interface Column {
  key: keyof Job;
  label: string;
  truncate?: boolean;
  width: number;
}

const COLUMNS: Column[] = [
  { key: 'url', label: 'URL', truncate: true, width: 70 },
  { key: 'secondaryUrl', label: 'Secondary URL', truncate: true, width: 70 },
  { key: 'companyName', label: 'Company name', width: 140 },
  { key: 'title', label: 'Title', width: 160 },
  { key: 'officialId', label: 'Official ID', width: 110 },
  { key: 'description', label: 'Description', truncate: true, width: 100 },
  { key: 'location', label: 'Location', width: 130 },
];

const CHECKBOX_COLUMN_WIDTH = 40;
const ACTIONS_COLUMN_WIDTH = 64;
const ID_COLUMN_WIDTH = 56;
const STATUS_COLUMN_WIDTH = 170;
const REFERRAL_STATUS_COLUMN_WIDTH = 220;
const MESSAGES_COLUMN_WIDTH = 224;

interface JobsTableProps {
  jobs: Job[];
  selectedIds: Set<number>;
  onToggleSelect: (id: number) => void;
  onEdit: (job: Job) => void;
}

export function JobsTable({
  jobs,
  selectedIds,
  onToggleSelect,
  onEdit,
}: JobsTableProps) {
  const { copy } = useClipboard();
  const { updateMutation } = useJobMutations();

  const handleStatusChange = (job: Job, status: string) => {
    updateMutation.mutate({
      id: job.id,
      payload: { status: status as Job['status'] },
    });
  };

  const handleReferralStatusChange = (job: Job, referralStatus: string) => {
    updateMutation.mutate({
      id: job.id,
      payload: { referralStatus: referralStatus as Job['referralStatus'] },
    });
  };

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead className={styles.thead}>
          <tr>
            <th
              className={`${styles.th} ${styles.checkboxCell}`}
              style={{ width: CHECKBOX_COLUMN_WIDTH }}
            />
            <th
              className={`${styles.th} ${styles.actionsCell}`}
              style={{ width: ACTIONS_COLUMN_WIDTH }}
            >
              Actions
            </th>
            <th
              className={`${styles.th} ${styles.cellWrap}`}
              style={{ width: ID_COLUMN_WIDTH }}
            >
              ID
            </th>
            <th
              className={`${styles.th} ${styles.cellTruncate}`}
              style={{ width: STATUS_COLUMN_WIDTH }}
            >
              Job Status
            </th>
            <th
              className={`${styles.th} ${styles.cellTruncate}`}
              style={{ width: REFERRAL_STATUS_COLUMN_WIDTH }}
            >
              Referral status
            </th>
            {COLUMNS.map((column) => (
              <th
                key={column.key}
                className={`${styles.th} ${column.truncate ? styles.cellTruncate : styles.cellWrap}`}
                style={{ width: column.width }}
              >
                {column.label}
              </th>
            ))}
            <th
              className={`${styles.th} ${styles.messagesCell}`}
              style={{ width: MESSAGES_COLUMN_WIDTH }}
            >
              Messages
            </th>
          </tr>
        </thead>
        <tbody className={styles.tbody}>
          {jobs.map((job) => (
            <tr key={job.id} className={styles.row}>
              <td
                className={styles.checkboxCell}
                style={{ width: CHECKBOX_COLUMN_WIDTH }}
              >
                <input
                  type="checkbox"
                  className={styles.checkbox}
                  checked={selectedIds.has(job.id)}
                  onChange={() => onToggleSelect(job.id)}
                />
              </td>
              <td
                className={styles.actionsCell}
                style={{ width: ACTIONS_COLUMN_WIDTH }}
              >
                <button
                  type="button"
                  className={styles.editButton}
                  onClick={() => onEdit(job)}
                  aria-label="Edit job"
                >
                  <Pencil size={16} />
                </button>
              </td>
              <td
                className={styles.cellWrap}
                style={{ width: ID_COLUMN_WIDTH }}
              >
                <button
                  type="button"
                  className={styles.copyButton}
                  onClick={() => copy(String(job.id))}
                  title="Click to copy"
                >
                  {job.id}
                </button>
              </td>
              <td
                className={styles.cellTruncate}
                style={{ width: STATUS_COLUMN_WIDTH }}
              >
                <div className={styles.statusCellInner}>
                  <Dropdown
                    label="Status"
                    hideLabel
                    value={job.status}
                    onChange={(value) => handleStatusChange(job, value)}
                    options={STATUS_DROPDOWN_OPTIONS}
                    highlighted={job.status === 'To Apply'}
                  />
                  {job.status === 'To Apply' ? (
                    <button
                      type="button"
                      className={styles.quickActionButton}
                      onClick={() => handleStatusChange(job, 'Applied')}
                      title="Mark as Applied"
                      aria-label="Mark as Applied"
                    >
                      <CheckCheck size={14} />
                    </button>
                  ) : null}
                </div>
              </td>
              <td
                className={styles.cellTruncate}
                style={{ width: REFERRAL_STATUS_COLUMN_WIDTH }}
              >
                <div className={styles.statusCellInner}>
                  <Dropdown
                    label="Referral status"
                    hideLabel
                    value={job.referralStatus}
                    onChange={(value) => handleReferralStatusChange(job, value)}
                    options={REFERRAL_STATUS_DROPDOWN_OPTIONS}
                    highlighted={job.referralStatus === 'Referral required'}
                  />
                  {job.referralStatus === 'Referral required' ? (
                    <button
                      type="button"
                      className={styles.quickActionButton}
                      onClick={() =>
                        handleReferralStatusChange(job, 'Referral asked')
                      }
                      title="Mark as Referral asked"
                      aria-label="Mark as Referral asked"
                    >
                      <CheckCheck size={14} />
                    </button>
                  ) : null}
                </div>
              </td>
              {COLUMNS.map((column) => {
                if (column.key === 'url' || column.key === 'secondaryUrl') {
                  const linkValue = job[column.key] as string | null;
                  return (
                    <td
                      key={column.key}
                      className={styles.cellTruncate}
                      style={{ width: column.width }}
                    >
                      {linkValue ? (
                        <button
                          type="button"
                          className={styles.urlButton}
                          onClick={() => copy(linkValue)}
                          title={linkValue}
                        >
                          {linkValue}
                        </button>
                      ) : null}
                    </td>
                  );
                }
                const value = job[column.key];
                return (
                  <td
                    key={column.key}
                    className={
                      column.truncate ? styles.cellTruncate : styles.cellWrap
                    }
                    style={{ width: column.width }}
                  >
                    {value ? (
                      <button
                        type="button"
                        className={styles.copyButton}
                        onClick={() => copy(String(value))}
                        title="Click to copy"
                      >
                        {value}
                      </button>
                    ) : null}
                  </td>
                );
              })}
              <td
                className={styles.messagesCell}
                style={{ width: MESSAGES_COLUMN_WIDTH }}
              >
                <MessageButtons jobs={[job]} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
