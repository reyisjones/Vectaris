/**
 * Frontend telemetry bootstrap.
 *
 * Initialises the OTel Web SDK and forwards Web Vitals (LCP, CLS, INP, FID, FCP, TTFB)
 * as OTel spans to the configured collector endpoint.
 *
 * Usage — import once at the top of main.tsx:
 *   import "./telemetry";
 */
import { context, trace } from "@opentelemetry/api";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { Resource } from "@opentelemetry/resources";
import {
  BatchSpanProcessor,
  ConsoleSpanExporter,
  SimpleSpanProcessor,
  WebTracerProvider,
} from "@opentelemetry/sdk-trace-web";
import { SEMRESATTRS_SERVICE_NAME, SEMRESATTRS_SERVICE_VERSION } from "@opentelemetry/semantic-conventions";
import { onCLS, onFCP, onFID, onINP, onLCP, onTTFB } from "web-vitals";

// ─── Configuration ────────────────────────────────────────────────────────────
const OTEL_COLLECTOR_URL =
  (import.meta as ImportMeta & { env: Record<string, string> }).env
    .VITE_OTEL_COLLECTOR_URL ?? "";
const DEBUG = (import.meta as ImportMeta & { env: Record<string, string> }).env
  .DEV === "true";

// ─── Provider ─────────────────────────────────────────────────────────────────
const resource = new Resource({
  [SEMRESATTRS_SERVICE_NAME]: "vectaris-frontend",
  [SEMRESATTRS_SERVICE_VERSION]: "1.0.0",
});

const provider = new WebTracerProvider({ resource });

if (OTEL_COLLECTOR_URL) {
  provider.addSpanProcessor(
    new BatchSpanProcessor(
      new OTLPTraceExporter({ url: `${OTEL_COLLECTOR_URL}/v1/traces` }),
    ),
  );
}

if (DEBUG) {
  provider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter()));
}

provider.register();

const tracer = trace.getTracer("vectaris-frontend", "1.0.0");

// ─── Web Vitals ───────────────────────────────────────────────────────────────
function reportVital(name: string, value: number, rating: string) {
  const span = tracer.startSpan(`web_vital.${name.toLowerCase()}`, {
    attributes: {
      "web_vital.name": name,
      "web_vital.value": value,
      "web_vital.rating": rating,
      "web_vital.unit": name === "CLS" ? "score" : "ms",
    },
  });
  span.end();
}

onLCP(({ name, value, rating }) => reportVital(name, value, rating));
onCLS(({ name, value, rating }) => reportVital(name, value, rating));
onFID(({ name, value, rating }) => reportVital(name, value, rating));
onINP(({ name, value, rating }) => reportVital(name, value, rating));
onFCP(({ name, value, rating }) => reportVital(name, value, rating));
onTTFB(({ name, value, rating }) => reportVital(name, value, rating));

export { context, tracer };
