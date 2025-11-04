import { useCallback, useEffect, useState } from 'react';

/** Function that fetches data for the lazy resource. */
export type ResourceLoader<TData> = () => Promise<TData>;

export interface LazyResourceOptions<TData> {
  /** Whether the resource should be refreshed automatically. */
  isActive: boolean;
  /** Initial placeholder value shown before the first load. */
  initialValue: TData;
}

export interface LazyResourceState<TData> {
  data: TData;
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

/**
 * Lazily loads data when {@link LazyResourceOptions.isActive} becomes true and exposes
 * refresh/error state for the caller.
 */
export function useLazyResource<TData>(
  loader: ResourceLoader<TData>,
  { isActive, initialValue }: LazyResourceOptions<TData>,
): LazyResourceState<TData> {
  const [data, setData] = useState(initialValue);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const next = await loader();
      setData(next);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [loader]);

  useEffect(() => {
    if (isActive) {
      void refresh();
    }
  }, [isActive, refresh]);

  return { data, loading, error, refresh };
}
