import { useEffect, useCallback } from 'react';
import { apiClient } from '@/utils/api';

export function useAnalytics() {
  const trackEvent = (event: string, metadata?: Record<string, unknown>) => {
    apiClient.analytics().track(event, metadata);
  };

  const trackPageView = useCallback(() => {
    trackEvent('page_view', {
      path: window.location.pathname,
      referrer: document.referrer,
    });
  }, []);

  useEffect(() => {
    trackPageView();
  }, [trackPageView]);

  return {
    trackEvent,
    trackPageView,
  };
}