/**
 * useMetricsStream — subscribe to the backend SSE live metrics feed.
 *
 * Replaces polling-based usage of React Query for real-time dashboards.
 * Falls back gracefully when the server is unreachable.
 *
 * Usage:
 *   const { usage, latency, connected, error } = useMetricsStream();
 */
import { useEffect, useRef, useState } from "react";

import {
  type LatencySummary,
  type MetricsStreamEvent,
  type UsageSummary,
  subscribeMetricsStream,
} from "../services/api";

export interface MetricsStreamState {
  usage: UsageSummary | null;
  latency: LatencySummary | null;
  /** true while the SSE connection is open and receiving events */
  connected: boolean;
  /** last connection error (cleared on reconnect) */
  error: string | null;
  /** ISO timestamp of the last received event */
  lastUpdated: string | null;
}

const RECONNECT_DELAY_MS = 5_000;

export function useMetricsStream(intervalSeconds = 5): MetricsStreamState {
  const [state, setState] = useState<MetricsStreamState>({
    usage: null,
    latency: null,
    connected: false,
    error: null,
    lastUpdated: null,
  });

  const cleanupRef = useRef<(() => void) | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let destroyed = false;

    function connect() {
      if (destroyed) return;

      const unsub = subscribeMetricsStream(
        (event: MetricsStreamEvent) => {
          setState({
            usage: event.usage,
            latency: event.latency,
            connected: true,
            error: null,
            lastUpdated: new Date().toISOString(),
          });
        },
        (_err) => {
          setState((prev) => ({
            ...prev,
            connected: false,
            error: "Stream disconnected — reconnecting…",
          }));

          // auto-reconnect after a short delay
          if (!destroyed) {
            reconnectRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
          }
        },
        intervalSeconds,
      );

      cleanupRef.current = unsub;
    }

    connect();

    return () => {
      destroyed = true;
      cleanupRef.current?.();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [intervalSeconds]);

  return state;
}
