import { useCallback, useEffect, useState } from 'react';

function readSearchParams(): URLSearchParams {
  return new URLSearchParams(window.location.search);
}

export function useUrlSearchParams(): [
  URLSearchParams,
  (next: URLSearchParams) => void,
] {
  const [searchParams, setSearchParamsState] = useState(readSearchParams);

  useEffect(() => {
    const handlePopState = () => setSearchParamsState(readSearchParams());
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const setSearchParams = useCallback((next: URLSearchParams) => {
    const query = next.toString();
    const url = query
      ? `${window.location.pathname}?${query}`
      : window.location.pathname;
    window.history.replaceState(null, '', url);
    setSearchParamsState(next);
  }, []);

  return [searchParams, setSearchParams];
}
