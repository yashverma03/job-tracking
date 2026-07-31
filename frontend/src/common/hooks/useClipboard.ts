import { useCallback } from 'react'
import toast from 'react-hot-toast'

export function useClipboard() {
  const copy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }, [])

  return { copy }
}
