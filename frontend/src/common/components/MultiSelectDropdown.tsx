import { useEffect, useRef, useState } from 'react';

import type { DropdownOption } from './Dropdown';
import styles from './MultiSelectDropdown.module.css';

interface MultiSelectDropdownProps {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  options: DropdownOption[];
  hideLabel?: boolean;
  emptyLabel?: string;
}

export function MultiSelectDropdown({
  label,
  values,
  onChange,
  options,
  hideLabel = false,
  emptyLabel = 'All',
}: MultiSelectDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleOutsideClick = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [isOpen]);

  const toggleValue = (value: string) => {
    if (values.includes(value)) {
      onChange(values.filter((item) => item !== value));
    } else {
      onChange([...values, value]);
    }
  };

  const summary =
    values.length === 0
      ? emptyLabel
      : values
          .map((value) => options.find((option) => option.value === value)?.label ?? value)
          .join(', ');

  return (
    <div className={styles.container} ref={containerRef}>
      {!hideLabel && <span className={styles.label}>{label}</span>}
      <button
        type="button"
        className={styles.trigger}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className={styles.triggerText}>{summary}</span>
        <span className={styles.arrow} aria-hidden="true">
          ▾
        </span>
      </button>
      {isOpen && (
        <div className={styles.menu} role="listbox">
          {options.map((option) => (
            <label key={option.value} className={styles.option}>
              <input
                type="checkbox"
                className={styles.checkbox}
                checked={values.includes(option.value)}
                onChange={() => toggleValue(option.value)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
