import { useCallback, useState } from 'react'

const COPIED_RESET_DELAY_MS = 2000

export function useClipboard() {
  const [copied, setCopied] = useState(false)

  const copy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), COPIED_RESET_DELAY_MS)
  }, [])

  return { copied, copy }
}
