import { useState, useCallback } from 'react';
import { LoadingState } from '@/types';

export function useLoadingState(initialLoading = false): [
  LoadingState,
  {
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    setProgress: (progress: number) => void;
    reset: () => void;
  }
] {
  const [state, setState] = useState<LoadingState>({
    isLoading: initialLoading,
    error: null,
    progress: undefined,
  });

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error, isLoading: false }));
  }, []);

  const setProgress = useCallback((progress: number) => {
    setState(prev => ({ ...prev, progress }));
  }, []);

  const reset = useCallback(() => {
    setState({ isLoading: false, error: null, progress: undefined });
  }, []);

  return [
    state,
    { setLoading, setError, setProgress, reset }
  ];
}