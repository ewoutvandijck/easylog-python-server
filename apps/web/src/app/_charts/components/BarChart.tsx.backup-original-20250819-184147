import {
  Bar,
  CartesianGrid,
  BarChart as RechartsBarChart,
  XAxis
} from 'recharts';

import ChartContainer from '@/app/_ui/components/Chart/ChartContainer';
import ChartLegend from '@/app/_ui/components/Chart/ChartLegend';
import ChartLegendContent from '@/app/_ui/components/Chart/ChartLegendContent';
import ChartTooltip from '@/app/_ui/components/Chart/ChartTooltip';
import ChartTooltipContent from '@/app/_ui/components/Chart/ChartTooltipContent';
import { ChartConfig } from '@/app/_ui/components/Chart/utils/chartConfig';

import { InternalChartConfig } from '../schemas/internalChartConfigSchema';

export interface BarChartProps {
  config: InternalChartConfig;
}

const BarChart = ({ config }: BarChartProps) => {
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
      <RechartsBarChart accessibilityLayer data={data}>
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
          <Bar
            key={s.dataKey}
            dataKey={s.dataKey}
            fill={s.color}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </RechartsBarChart>
    </ChartContainer>
  );
};

export default BarChart;
