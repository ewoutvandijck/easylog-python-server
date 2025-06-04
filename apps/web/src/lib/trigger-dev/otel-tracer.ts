import { Span, SpanOptions, Tracer } from '@opentelemetry/api';
import { logger } from '@trigger.dev/sdk';

const triggerDevOtelTracer = {
  startSpan: logger.startSpan,
  startActiveSpan: <F extends (span: Span) => Promise<unknown>>(
    name: string,
    options: SpanOptions,
    fn: F
  ) => {
    const span = logger.startSpan(name, options);
    return fn ? fn(span) : Promise.resolve();
  },
  trace: logger.trace
} as unknown as Tracer;

export default triggerDevOtelTracer;
