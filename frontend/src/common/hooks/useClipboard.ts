import { useCallback } from 'react';
import toast from 'react-hot-toast';

export function useClipboard() {
  const copy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text);
    toast.success('Copied', {
      icon: null,
      style: {
        minHeight: 'auto',
        padding: '4px 10px',
        fontSize: '12px',
      },
    });
  }, []);

  return { copy };
}
