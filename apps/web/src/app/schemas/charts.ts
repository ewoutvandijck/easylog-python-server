import { z } from 'zod';

/** Supported chart types */
export const ChartType = z.enum(['bar', 'line', 'pie', 'donut']);
export type ChartType = z.infer<typeof ChartType>;

/** Styling configuration for chart elements */
export const styleConfigSchema = z
  .object({
    color: z.string().nullable().optional(),
    fill: z.string().nullable().optional(),
    opacity: z.number().nullable().optional().default(0.9),
    stroke_width: z.number().nullable().optional().default(2),
    stroke_dasharray: z.string().nullable().optional(),
    radius: z.number().nullable().optional().default(80),
    inner_radius: z.number().nullable().optional().default(40) // For donut charts
  })
  .nullable()
  .optional();
export type StyleConfig = z.infer<typeof styleConfigSchema>;

/** Configuration for chart tooltips */
export const tooltipConfigSchema = z
  .object({
    show: z.boolean().optional().default(true),
    custom_content: z.string().nullable().optional(),
    hide_label: z.boolean().optional().default(false)
  })
  .nullable()
  .optional();
export type TooltipConfig = z.infer<typeof tooltipConfigSchema>;

/** Configuration for a data series in a chart */
export const seriesConfigSchema = z.object({
  label: z.string(),
  data_key: z.string(),
  style: styleConfigSchema.optional().default({}),
  stack_id: z.string().nullable().optional()
  // Removed type field as it's no longer needed for single-type charts
});
export type SeriesConfig = z.infer<typeof seriesConfigSchema>;

/** Configuration for chart axes */
export const axisConfigSchema = z
  .object({
    show: z.boolean().optional().default(true),
    label: z.string().nullable().optional(),
    tick_line: z.boolean().optional().default(true),
    tick_margin: z.number().optional().default(10),
    axis_line: z.boolean().optional().default(true),
    grid_lines: z.boolean().optional().default(true),
    formatter: z.string().nullable().optional()
  })
  .nullable()
  .optional();
export type AxisConfig = z.infer<typeof axisConfigSchema>;

/** Margin configuration for charts */
export const marginConfigSchema = z
  .object({
    top: z.number().optional().default(0),
    right: z.number().optional().default(0),
    bottom: z.number().optional().default(0),
    left: z.number().optional().default(0)
  })
  .nullable()
  .optional();
export type MarginConfig = z.infer<typeof marginConfigSchema>;

/** Complete chart configuration */
export const chartConfigSchema = z.object({
  type: ChartType,
  title: z.string(),
  description: z.string().nullish(),
  data: z.array(z.record(z.any())),
  series: z.array(seriesConfigSchema),
  x_axis: axisConfigSchema.optional().default({}),
  y_axis: axisConfigSchema.optional().default({}),
  style: styleConfigSchema.optional().default({}),
  tooltip: tooltipConfigSchema.optional().default({}),
  legend: z.boolean().optional().default(true),
  active_index: z.number().nullish(),
  animation: z.boolean().optional().default(true),
  width: z.number().nullish(),
  height: z.number().nullish().default(400),
  margin: marginConfigSchema.optional().default({})
});
export type ChartConfig = z.infer<typeof chartConfigSchema>;
