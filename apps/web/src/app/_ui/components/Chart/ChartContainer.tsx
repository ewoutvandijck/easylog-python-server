import { createContext, useId } from 'react';
import * as RechartsPrimitive from 'recharts';
import { VariantProps, tv } from 'tailwind-variants';

import ChartStyle from './ChartStyle';
import { ChartConfig } from './utils/chartConfig';

export const chartStyles = tv({
  base: '[&_.recharts-cartesian-axis-tick_text]:fill-text-muted [&_.recharts-cartesian-grid_line[stroke="#ccc"]]:stroke-border-primary/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border-primary [&_.recharts-polar-grid_[stroke="#ccc"]]:stroke-border-primary [&_.recharts-radial-bar-background-sector]:fill-fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-fill-muted [&_.recharts-reference-line_[stroke="#ccc"]]:stroke-border-primary flex aspect-video justify-center text-xs [&_.recharts-dot[stroke="#fff"]]:stroke-transparent [&_.recharts-layer]:outline-none [&_.recharts-sector[stroke="#fff"]]:stroke-transparent [&_.recharts-sector]:outline-none [&_.recharts-surface]:outline-none'
});

export interface ChartProps
  extends React.ComponentProps<'div'>,
    VariantProps<typeof chartStyles> {
  config: ChartConfig;
  children: React.ComponentProps<
    typeof RechartsPrimitive.ResponsiveContainer
  >['children'];
}

type ChartContextProps = {
  config: ChartConfig;
};

export const ChartContext = createContext<ChartContextProps | null>(null);

const ChartContainer = ({
  id,
  className,
  children,
  config,
  ...props
}: ChartProps) => {
  const uniqueId = useId();
  const chartId = `chart-${id || uniqueId.replace(/:/g, '')}`;

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-chart={chartId}
        className={chartStyles({ className })}
        {...props}
      >
        <ChartStyle id={chartId} config={config} />
        <RechartsPrimitive.ResponsiveContainer>
          {children}
        </RechartsPrimitive.ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  );
};

export default ChartContainer;
