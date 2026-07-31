import type { ChangeEvent } from 'react'

import styles from './Dropdown.module.css'

export interface DropdownOption {
  value: string
  label: string
}

interface DropdownProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: DropdownOption[]
  allowEmpty?: boolean
  emptyLabel?: string
}

export function Dropdown({
  label,
  value,
  onChange,
  options,
  allowEmpty = false,
  emptyLabel = 'All',
}: DropdownProps) {
  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onChange(event.target.value)
  }

  return (
    <label className={styles.container}>
      <span className={styles.label}>{label}</span>
      <div className={styles.selectWrapper}>
        <select className={styles.select} value={value} onChange={handleChange}>
          {allowEmpty && <option value="">{emptyLabel}</option>}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <span className={styles.arrow} aria-hidden="true">
          ▾
        </span>
      </div>
    </label>
  )
}
