import axios from 'axios';

export function extractErrorMessage(error: unknown): string | undefined {
  if (!axios.isAxiosError(error)) return undefined;
  const data = error.response?.data;
  return data && typeof data === 'object' && typeof data.message === 'string'
    ? data.message
    : undefined;
}
