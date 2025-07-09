import * as RechartsPrimitive from 'recharts';
import { VariantProps, tv } from 'tailwind-variants';

import useChart from './hooks/useChart';
import getPayloadConfigFromPayload from './utils/getPayloadConfigFromPayload';

export const chartLegendContentStyles = tv({
  slots: {
    root: 'flex items-center justify-center gap-4',
    item: '[&>svg]:text-text-muted flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3',
    itemIcon: 'h-2 w-2 shrink-0 rounded-[2px]'
  },
  variants: {
    verticalAlign: {
      top: {
        root: 'pb-3'
      },
      bottom: {
        root: 'pt-3'
      },
      middle: {
        root: 'pt-3'
      }
    }
  },
  defaultVariants: {
    verticalAlign: 'middle'
  }
});

export interface ChartLegendContentProps
  extends React.ComponentProps<'div'>,
    VariantProps<typeof chartLegendContentStyles>,
    Pick<RechartsPrimitive.LegendProps, 'payload'> {
  hideIcon?: boolean;
  nameKey?: string;
}

const {
  root: rootStyles,
  item: itemStyles,
  itemIcon: itemIconStyles
} = chartLegendContentStyles();

const ChartLegendContent = ({
  className,
  hideIcon = false,
  payload,
  verticalAlign = 'bottom',
  nameKey
}: ChartLegendContentProps) => {
  const { config } = useChart();

  if (!payload?.length) {
    return null;
  }

  return (
    <div className={rootStyles({ className, verticalAlign })}>
      {payload.map((item) => {
        const key = `${nameKey || item.dataKey || 'value'}`;
        const itemConfig = getPayloadConfigFromPayload(config, item, key);

        return (
          <div key={item.value} className={itemStyles()}>
            {itemConfig?.icon && !hideIcon ? (
              <itemConfig.icon />
            ) : (
              <div
                className={itemIconStyles()}
                style={{
                  backgroundColor: item.color
                }}
              />
            )}
            {itemConfig?.label}
          </div>
        );
      })}
    </div>
  );
};

export default ChartLegendContent;
