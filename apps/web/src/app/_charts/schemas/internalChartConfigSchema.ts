import { z } from 'zod';

const internalChartConfigSchema = z.object({
  type: z.enum(['stacked-bar']),
  /**
   * Use the code below to define the `data` field instead of z.record to fix
   *
   * - "Invalid schema for function 'createChart': Extra required key 'data'
   *   supplied."
   *
   * The catch-all pattern below keeps the same runtime behaviour (accept
   * arbitrary key/value objects) but produces a schema that passes the stricter
   * validation.
   */
  data: z.array(
    z
      .object({})
      .catchall(z.union([z.number(), z.string()]))
      .strict()
  ),
  xAxisKey: z.string(),
  series: z.array(
    z.object({
      dataKey: z.string(),
      label: z.string(),
      color: z.enum(['chart-1', 'chart-2', 'chart-3', 'chart-4', 'chart-5'])
    })
  )
});

export type InternalChartConfig = z.infer<typeof internalChartConfigSchema>;

export default internalChartConfigSchema;
