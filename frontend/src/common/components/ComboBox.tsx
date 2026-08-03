import { useEffect, useRef, useState, type FocusEvent } from 'react'

import styles from './ComboBox.module.css'

interface ComboBoxProps {
  label: string
  value: string
  onChange: (value: string) => void
  onBlur?: (event: FocusEvent<HTMLInputElement>) => void
  options: string[]
  hideLabel?: boolean
  className?: string
}

export function ComboBox({ label, value, onChange, onBlur, options, hideLabel = false, className }: ComboBoxProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  const handleSelect = (option: string) => {
    onChange(option)
    setIsOpen(false)
  }

  return (
    <div className={`${styles.container} ${className ?? ''}`} ref={containerRef}>
      {!hideLabel && <span className={styles.label}>{label}</span>}
      <input
        className={styles.input}
        value={value}
        onFocus={() => setIsOpen(true)}
        onChange={(event) => {
          onChange(event.target.value)
          setIsOpen(true)
        }}
        onBlur={onBlur}
      />
      {isOpen && (
        <div className={styles.menu}>
          {options.length === 0 && <div className={styles.emptyState}>No matches</div>}
          {options.map((option) => (
            <button
              key={option}
              type="button"
              className={styles.option}
              onMouseDown={(event) => {
                event.preventDefault()
                handleSelect(option)
              }}
            >
              {option}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
