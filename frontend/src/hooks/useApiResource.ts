"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { isDemoFallbackEnabled } from "@/lib/api/client";

export type DataSource = "api" | "fallback" | "error" | "loading";

interface UseApiResourceOptions<T> {
  loader: () => Promise<T>;
  fallback: () => T;
  enabled?: boolean;
}

interface UseApiResourceResult<T> {
  data: T | null;
  error: string | null;
  source: DataSource;
  isLoading: boolean;
  isFallback: boolean;
  reload: () => void;
}

export function useApiResource<T>({
  loader,
  fallback,
  enabled = true,
}: UseApiResourceOptions<T>): UseApiResourceResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<DataSource>("loading");
  const [isLoading, setIsLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);
  const warnedRef = useRef(false);

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let cancelled = false;

    async function run() {
      setIsLoading(true);
      setError(null);
      setSource("loading");

      try {
        const result = await loader();
        if (cancelled) return;
        setData(result);
        setSource("api");
        setIsLoading(false);
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof Error ? err.message : "Unable to reach the SafetyLens API.";

        if (isDemoFallbackEnabled()) {
          if (!warnedRef.current && process.env.NODE_ENV === "development") {
            console.warn(
              "[SafetyLens] API unavailable — activating Offline Demo Mode fallback.",
              message
            );
            warnedRef.current = true;
          }
          setData(fallback());
          setError(message);
          setSource("fallback");
          setIsLoading(false);
          return;
        }

        setData(null);
        setError(message);
        setSource("error");
        setIsLoading(false);
      }
    }

    void run();

    return () => {
      cancelled = true;
    };
  }, [enabled, fallback, loader, reloadToken]);

  return {
    data,
    error,
    source,
    isLoading,
    isFallback: source === "fallback",
    reload,
  };
}
