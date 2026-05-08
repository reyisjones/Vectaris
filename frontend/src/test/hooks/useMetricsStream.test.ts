import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useMetricsStream } from "../../hooks/useMetricsStream";
import * as api from "../../services/api";

// Minimal EventSource mock
class MockEventSource {
  static instances: MockEventSource[] = [];

  onmessage: ((e: { data: string }) => void) | null = null;
  onerror: ((e: Event) => void) | null = null;
  private closed = false;

  constructor(public url: string) {
    MockEventSource.instances.push(this);
  }

  close() {
    this.closed = true;
  }

  /** Helper used in tests to simulate a server push */
  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  /** Helper used in tests to simulate a connection error */
  simulateError() {
    this.onerror?.(new Event("error"));
  }
}

const mockUsage: api.UsageSummary = {
  total_requests: 1000,
  total_tokens: 400000,
  error_rate: 0.01,
  models: [],
};
const mockLatency: api.LatencySummary = { models: [] };

describe("useMetricsStream", () => {
  let subscribeSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    MockEventSource.instances = [];

    subscribeSpy = vi.spyOn(api, "subscribeMetricsStream").mockImplementation(
      (onData, onError) => {
        const src = new MockEventSource("http://localhost/api/v1/metrics/stream");

        src.onmessage = (e) => {
          try {
            onData(JSON.parse(e.data));
          } catch {
            // ignore
          }
        };
        if (onError) src.onerror = onError;

        // Return cleanup
        return () => src.close();
      },
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllTimers();
  });

  it("starts with disconnected state", () => {
    const { result } = renderHook(() => useMetricsStream());
    expect(result.current.connected).toBe(false);
    expect(result.current.usage).toBeNull();
    expect(result.current.latency).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("updates state when an event is received", () => {
    const { result } = renderHook(() => useMetricsStream());

    act(() => {
      MockEventSource.instances[0]?.simulateMessage({ usage: mockUsage, latency: mockLatency });
    });

    expect(result.current.connected).toBe(true);
    expect(result.current.usage?.total_requests).toBe(1000);
    expect(result.current.latency?.models).toEqual([]);
    expect(result.current.error).toBeNull();
    expect(result.current.lastUpdated).not.toBeNull();
  });

  it("sets error state on connection error", () => {
    const { result } = renderHook(() => useMetricsStream());

    act(() => {
      MockEventSource.instances[0]?.simulateError();
    });

    expect(result.current.connected).toBe(false);
    expect(result.current.error).toMatch(/reconnecting/i);
  });

  it("clears error after receiving a successful event", () => {
    const { result } = renderHook(() => useMetricsStream());

    act(() => {
      MockEventSource.instances[0]?.simulateError();
    });
    expect(result.current.error).not.toBeNull();

    act(() => {
      MockEventSource.instances[0]?.simulateMessage({ usage: mockUsage, latency: mockLatency });
    });
    expect(result.current.error).toBeNull();
  });

  it("calls subscribeMetricsStream with correct interval", () => {
    renderHook(() => useMetricsStream(10));
    expect(subscribeSpy).toHaveBeenCalledWith(
      expect.any(Function),
      expect.any(Function),
      10,
    );
  });
});
