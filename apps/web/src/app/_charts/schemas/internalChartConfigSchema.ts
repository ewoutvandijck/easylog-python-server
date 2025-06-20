import { z } from 'zod';

const internalChartConfigSchema = z.object({
  type: z.enum(['stacked-bar']),
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
      color: z.enum([
        'var(--color-chart-1)',
        'var(--color-chart-2)',
        'var(--color-chart-3)',
        'var(--color-chart-4)',
        'var(--color-chart-5)'
      ])
    })
  )
});

export type InternalChartConfig = z.infer<typeof internalChartConfigSchema>;

export default internalChartConfigSchema;
