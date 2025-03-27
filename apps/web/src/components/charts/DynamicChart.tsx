'use client';

import {
  Bar,
  BarChart,
  Line,
  LineChart,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  XAxis,
  YAxis
} from 'recharts';
import { ChartConfig, chartConfigSchema } from '@/app/schemas/charts';
import { ChartContainer } from '@/components/ui/chart';
import { ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { ChartLegend, ChartLegendContent } from '@/components/ui/chart';

interface DynamicChartProps {
  chartJson: string;
}

// Helper function to convert null to undefined for props
// recharts doesn't handle null well, but requires undefined
const nullToUndefined = <T,>(value: T | null | undefined): T | undefined => {
  return value === null ? undefined : value;
};

export function DynamicChart({ chartJson }: DynamicChartProps) {
  let chartConfig: ChartConfig;

  try {
    const parsed = JSON.parse(chartJson);
    chartConfig = chartConfigSchema.parse(parsed);
  } catch (e) {
    console.error('Invalid chart configuration:', e);
    return (
      <div className="w-full rounded-lg border bg-card p-4 overflow-hidden">
        <div className="flex flex-col gap-2">
          <h3 className="font-semibold">Invalid chart configuration</h3>
          <p className="text-sm text-muted-foreground">
            {e instanceof Error ? e.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  // Convert our chart config to shadcn's format
  const shadcnConfig = chartConfig.series.reduce(
    (acc, series, index) => {
      acc[series.data_key] = {
        label: series.label,
        color:
          nullToUndefined(series.style?.color) ||
          nullToUndefined(series.style?.fill) ||
          `hsl(var(--chart-${index + 1}))`
      };
      return acc;
    },
    {} as Record<string, { label: string; color: string }>
  );

  // Get dimensions and margin from config or use defaults
  const height = chartConfig.height || 300;
  const margin = chartConfig.margin || {
    top: 0,
    right: 0,
    bottom: 0,
    left: 0
  };

  // For pie/donut charts, use larger margins by default
  const pieMargin =
    chartConfig.type === 'pie' || chartConfig.type === 'donut'
      ? chartConfig.margin || {
          top: 0,
          right: 0,
          bottom: 0,
          left: 0
        }
      : margin;

  const showTooltip = chartConfig.tooltip?.show !== false;
  const showLegend = chartConfig.legend !== false;
  const animationDuration = chartConfig.animation !== false ? 1500 : 0;

  return (
    <div className="w-full rounded-lg border bg-card p-4 overflow-hidden">
      <div className="flex flex-col gap-2">
        <h3 className="font-semibold">{chartConfig.title}</h3>
        {chartConfig.description && (
          <p className="text-sm text-muted-foreground">
            {chartConfig.description}
          </p>
        )}
      </div>

      <div className="mt-4 w-full">
        {/* BAR CHART */}
        {chartConfig.type === 'bar' && (
          <ChartContainer
            config={shadcnConfig}
            style={{ minHeight: `${height}px` }}
            className="w-full"
          >
            <BarChart
              data={chartConfig.data}
              margin={margin}
              accessibilityLayer
            >
              {chartConfig.x_axis?.grid_lines !== false && (
                <CartesianGrid vertical={false} />
              )}
              <XAxis
                dataKey={chartConfig.series[0].data_key}
                tickLine={chartConfig.x_axis?.tick_line}
                tickMargin={chartConfig.x_axis?.tick_margin || 10}
                axisLine={chartConfig.x_axis?.axis_line}
              />
              <YAxis width={40} />
              {showTooltip && (
                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      hideLabel={chartConfig.tooltip?.hide_label}
                    />
                  }
                />
              )}
              {showLegend && <ChartLegend content={<ChartLegendContent />} />}

              {/* Skip the first series (index 0) which is used for the x-axis */}
              {chartConfig.series.slice(1).map((series) => (
                <Bar
                  key={series.data_key}
                  dataKey={series.data_key}
                  name={series.label}
                  fill={`var(--color-${series.data_key})`}
                  stroke={
                    nullToUndefined(series.style?.color) ||
                    `var(--color-${series.data_key})`
                  }
                  strokeWidth={nullToUndefined(series.style?.stroke_width) || 0}
                  strokeDasharray={nullToUndefined(
                    series.style?.stroke_dasharray
                  )}
                  opacity={nullToUndefined(series.style?.opacity) || 1}
                  radius={nullToUndefined(series.style?.radius) || 4}
                  stackId={nullToUndefined(series.stack_id)}
                  animationDuration={animationDuration}
                />
              ))}
            </BarChart>
          </ChartContainer>
        )}

        {/* LINE CHART */}
        {chartConfig.type === 'line' && (
          <ChartContainer
            config={shadcnConfig}
            style={{ minHeight: `${height}px` }}
            className="w-full"
          >
            <LineChart
              data={chartConfig.data}
              margin={margin}
              accessibilityLayer
            >
              {chartConfig.x_axis?.grid_lines !== false && (
                <CartesianGrid vertical={false} />
              )}
              <XAxis
                dataKey={chartConfig.series[0].data_key}
                tickLine={chartConfig.x_axis?.tick_line}
                tickMargin={chartConfig.x_axis?.tick_margin || 10}
                axisLine={chartConfig.x_axis?.axis_line}
              />
              <YAxis width={40} />
              {showTooltip && (
                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      hideLabel={chartConfig.tooltip?.hide_label}
                    />
                  }
                />
              )}
              {showLegend && <ChartLegend content={<ChartLegendContent />} />}

              {/* Skip the first series (index 0) which is used for the x-axis */}
              {chartConfig.series.slice(1).map((series) => (
                <Line
                  key={series.data_key}
                  type="monotone"
                  dataKey={series.data_key}
                  name={series.label}
                  stroke={`var(--color-${series.data_key})`}
                  strokeWidth={nullToUndefined(series.style?.stroke_width) || 2}
                  strokeDasharray={nullToUndefined(
                    series.style?.stroke_dasharray
                  )}
                  opacity={nullToUndefined(series.style?.opacity) || 1}
                  dot={{
                    r: nullToUndefined(series.style?.radius) || 4
                  }}
                  activeDot={{
                    r: nullToUndefined(series.style?.radius)
                      ? Math.min(
                          (nullToUndefined(series.style?.radius) || 4) + 2,
                          8
                        )
                      : 6
                  }}
                  animationDuration={animationDuration}
                />
              ))}
            </LineChart>
          </ChartContainer>
        )}

        {/* PIE/DONUT CHART */}
        {(chartConfig.type === 'pie' || chartConfig.type === 'donut') && (
          <ChartContainer
            config={shadcnConfig}
            style={{ minHeight: `${height}px` }}
            className="w-full"
          >
            <PieChart margin={pieMargin} accessibilityLayer>
              <Pie
                data={chartConfig.data}
                dataKey={chartConfig.series[0].data_key}
                nameKey={chartConfig.series[0].label}
                cx="50%"
                cy="50%"
                outerRadius={
                  nullToUndefined(chartConfig.series[0].style?.radius) || 80
                }
                innerRadius={
                  chartConfig.type === 'donut'
                    ? nullToUndefined(
                        chartConfig.series[0].style?.inner_radius
                      ) || 40
                    : 0
                }
                paddingAngle={3}
                animationDuration={animationDuration}
                label={({ name, percent }) => {
                  // Only show percentage on larger segments (>= 5%)
                  return percent >= 0.05
                    ? `${name}: ${(percent * 100).toFixed(0)}%`
                    : '';
                }}
                labelLine={{
                  stroke: 'var(--muted-foreground)',
                  strokeWidth: 1,
                  strokeDasharray: ''
                }}
              >
                {chartConfig.data.map((entry, index) => {
                  // Calculate which color to use
                  const colorIndex = (index % 5) + 1;
                  const colorVar = `var(--color-${entry[chartConfig.series[0].data_key]})`;
                  const fallbackColor = `hsl(var(--chart-${colorIndex}))`;

                  // Get the fill color first
                  const fillColor =
                    nullToUndefined(entry.fill) || colorVar || fallbackColor;

                  return (
                    <Cell
                      key={`cell-${index}`}
                      fill={fillColor}
                      stroke="white" // Use white stroke for better segment separation
                      strokeWidth={1}
                      strokeDasharray={nullToUndefined(
                        chartConfig.series[0].style?.stroke_dasharray
                      )}
                      opacity={
                        nullToUndefined(chartConfig.series[0].style?.opacity) ||
                        1
                      }
                    />
                  );
                })}
              </Pie>
              {showTooltip && (
                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      hideLabel={chartConfig.tooltip?.hide_label}
                      nameKey={chartConfig.series[0].label}
                    />
                  }
                />
              )}
              {showLegend && (
                <ChartLegend
                  content={
                    <ChartLegendContent nameKey={chartConfig.series[0].label} />
                  }
                />
              )}
            </PieChart>
          </ChartContainer>
        )}
      </div>
    </div>
  );
}
