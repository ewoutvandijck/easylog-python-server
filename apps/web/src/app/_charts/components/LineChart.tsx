import {
  CartesianGrid,
  Line,
  LineChart as RechartsLineChart,
  XAxis
} from 'recharts';

import ChartContainer from '@/app/_ui/components/Chart/ChartContainer';
import ChartLegend from '@/app/_ui/components/Chart/ChartLegend';
import ChartLegendContent from '@/app/_ui/components/Chart/ChartLegendContent';
import ChartTooltip from '@/app/_ui/components/Chart/ChartTooltip';
import ChartTooltipContent from '@/app/_ui/components/Chart/ChartTooltipContent';
import { ChartConfig } from '@/app/_ui/components/Chart/utils/chartConfig';

import { InternalChartConfig } from '../schemas/internalChartConfigSchema';

export interface LineChartProps {
  config: InternalChartConfig;
}

const LineChart = ({ config }: LineChartProps) => {
  const { series, xAxisKey, data } = config;

  const chartConfig = series.reduce((acc, item) => {
    acc[item.dataKey] = {
      label: item.label,
      color: item.color
    };
    return acc;
  }, {} as ChartConfig);

  return (
    <ChartContainer config={chartConfig}>
      <RechartsLineChart accessibilityLayer data={data}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey={xAxisKey}
          tickLine={false}
          tickMargin={10}
          axisLine={false}
          tickFormatter={(value) => value.slice(0, 3)}
        />
        <ChartTooltip content={<ChartTooltipContent hideLabel />} />
        <ChartLegend content={<ChartLegendContent />} />
        {series.map((s) => (
          <Line
            key={s.dataKey}
            dataKey={s.dataKey}
            stroke={s.color}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </RechartsLineChart>
    </ChartContainer>
  );
};

export default LineChart;
