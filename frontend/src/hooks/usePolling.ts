import { useCallback, useEffect, useRef, useState } from "react";

interface PollingState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

export function usePolling<T>(fetchFn: () => Promise<T>, intervalMs = 15000) {
  const [state, setState] = useState<PollingState<T>>({
    data: null,
    error: null,
    loading: true,
  });

  // Holds the latest fetchFn so the interval below doesn't need to restart
  // every time the caller passes a new closure.
  const fetchFnRef = useRef(fetchFn);
  fetchFnRef.current = fetchFn;

  // Shared across every tick (not per-call) so unmounting mid-flight cancels
  // whichever fetch is currently in progress, not just the first one.
  const cancelledRef = useRef(false);

  const refresh = useCallback(() => {
    setState((prev) => ({ ...prev, loading: true }));
    fetchFnRef
      .current()
      .then((data) => {
        if (!cancelledRef.current) setState({ data, error: null, loading: false });
      })
      .catch((err: unknown) => {
        if (!cancelledRef.current) {
          const message = err instanceof Error ? err.message : "Request failed";
          setState((prev) => ({ ...prev, error: message, loading: false }));
        }
      });
  }, []);

  useEffect(() => {
    cancelledRef.current = false;
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => {
      cancelledRef.current = true;
      clearInterval(id);
    };
  }, [intervalMs, refresh]);

  return { ...state, refresh };
}
