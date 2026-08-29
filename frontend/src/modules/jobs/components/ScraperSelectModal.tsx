import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X } from 'lucide-react';

import { fetchScraperNameOptions } from '../../../common/api/jobs/jobs.service';
import { MultiSelectDropdown } from '../../../common/components/MultiSelectDropdown';
import styles from './ScraperSelectModal.module.css';

interface ScraperSelectModalProps {
  onClose: () => void;
  onConfirm: (scraperNames: string[]) => void;
  isSubmitting: boolean;
}

export function ScraperSelectModal({ onClose, onConfirm, isSubmitting }: ScraperSelectModalProps) {
  const [selected, setSelected] = useState<string[]>([]);
  const { data: options = [], isLoading } = useQuery({
    queryKey: ['scraper-names'],
    queryFn: fetchScraperNameOptions,
  });

  const handleConfirm = () => {
    onConfirm(selected);
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
          <button type="button" className={styles.closeButton} onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {isLoading ? (
          <p className={styles.hint}>Loading scrapers...</p>
        ) : (
          <MultiSelectDropdown
            label="Scrapers"
            values={selected}
            onChange={setSelected}
            options={options}
            emptyLabel="All scrapers"
          />
        )}

        <div className={styles.actions}>
          <button type="button" className={styles.cancelButton} onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className={styles.submitButton}
            onClick={handleConfirm}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Queuing...' : 'Run'}
          </button>
        </div>
      </div>
    </div>
  );
}
