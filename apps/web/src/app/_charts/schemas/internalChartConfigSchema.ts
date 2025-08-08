import { z } from 'zod';

const internalChartConfigSchema = z.object({
  type: z.enum(['stacked-bar', 'bar', 'line', 'pie']),
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
      color: z
        .string()
        .describe(
          'The color of the series, can either be a valid hex or RGB color, e.g. #000000 or rgb(0, 0, 0), or a CSS variable, e.g. var(--color-chart-1). We have 5 colors available: var(--color-chart-1), var(--color-chart-2), var(--color-chart-3), var(--color-chart-4), var(--color-chart-5).'
        )
    })
  )
});

export type InternalChartConfig = z.infer<typeof internalChartConfigSchema>;

export default internalChartConfigSchema;
