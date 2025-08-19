import { Cell, Pie, PieChart as RechartsPieChart } from 'recharts';

import ChartContainer from '@/app/_ui/components/Chart/ChartContainer';
import ChartLegend from '@/app/_ui/components/Chart/ChartLegend';
import ChartLegendContent from '@/app/_ui/components/Chart/ChartLegendContent';
import ChartTooltip from '@/app/_ui/components/Chart/ChartTooltip';
import ChartTooltipContent from '@/app/_ui/components/Chart/ChartTooltipContent';
import { ChartConfig } from '@/app/_ui/components/Chart/utils/chartConfig';

import { InternalChartConfig } from '../schemas/internalChartConfigSchema';

export interface PieChartProps {
  config: InternalChartConfig;
}

const PieChart = ({ config }: PieChartProps) => {
  const { series, xAxisKey, data } = config;

  // Build legend config per category to ensure correct label-color mapping per segment
  const chartConfig = data.reduce((acc, datum, index) => {
    const categoryKey = String(datum[xAxisKey as keyof typeof datum]);
    const seriesForIndex = series[index] ?? series[index % series.length] ?? series[0];
    acc[categoryKey] = {
      label: seriesForIndex?.label ?? categoryKey,
      color: seriesForIndex?.color
    };
    return acc;
  }, {} as ChartConfig);

  // Assuming the first series is the one to display in the pie chart
  const pieSeries = series[0];
  const colors = series.map((s) => s.color);

  return (
    <ChartContainer config={chartConfig}>
      <RechartsPieChart>
        <ChartTooltip content={<ChartTooltipContent hideLabel />} />
        <Pie
          data={data}
          dataKey={pieSeries.dataKey}
          nameKey={xAxisKey}
          innerRadius={60}
          strokeWidth={5}
          stroke="var(--card)"
        >
          {data.map((_, index) => {
            return (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            );
          })}
        </Pie>
        <ChartLegend content={<ChartLegendContent nameKey={xAxisKey} />} />
      </RechartsPieChart>
    </ChartContainer>
  );
};

export default PieChart;
