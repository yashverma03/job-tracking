import { Dropdown } from '../../../common/components/Dropdown';
import {
  REFERRAL_STATUS_DROPDOWN_OPTIONS,
  STATUS_DROPDOWN_OPTIONS,
} from '../constants/job.constants';
import { useJobMutations } from '../hooks/useJobMutations';
import { MessageButtons } from './MessageButtons';
import type { Job } from '../types/job.types';
import styles from './BulkActionsBar.module.css';

interface BulkActionsBarProps {
  selectedJobs: Job[];
}

export function BulkActionsBar({ selectedJobs }: BulkActionsBarProps) {
  const isVisible = selectedJobs.length >= 2;
  const { bulkUpdateMutation } = useJobMutations();

  const handleBulkStatusChange = (status: string) => {
    bulkUpdateMutation.mutate({
      ids: selectedJobs.map((job) => job.id),
      payload: { status: status as Job['status'] },
    });
  };

  const handleBulkReferralStatusChange = (referralStatus: string) => {
    bulkUpdateMutation.mutate({
      ids: selectedJobs.map((job) => job.id),
      payload: { referralStatus: referralStatus as Job['referralStatus'] },
    });
  };

  return (
    <div
      className={styles.container}
      style={{ visibility: isVisible ? 'visible' : 'hidden' }}
    >
      <span className={styles.count}>{selectedJobs.length} jobs selected</span>
      <div className={styles.actions}>
        <div className={styles.dropdownGroup}>
          <Dropdown
            label="Set status"
            hideLabel
            value=""
            allowEmpty
            emptyLabel="Set status..."
            onChange={handleBulkStatusChange}
            options={STATUS_DROPDOWN_OPTIONS}
          />
          <Dropdown
            label="Set referral status"
            hideLabel
            value=""
            allowEmpty
            emptyLabel="Set referral status..."
            onChange={handleBulkReferralStatusChange}
            options={REFERRAL_STATUS_DROPDOWN_OPTIONS}
          />
        </div>
        <MessageButtons jobs={isVisible ? selectedJobs : []} />
      </div>
    </div>
  );
}
