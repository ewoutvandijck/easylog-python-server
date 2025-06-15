import { z } from 'zod';

const internalChartConfigSchema = z.object({
  type: z.enum(['stacked-bar']),
  data: z.array(z.record(z.string(), z.number().or(z.string()))),
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
