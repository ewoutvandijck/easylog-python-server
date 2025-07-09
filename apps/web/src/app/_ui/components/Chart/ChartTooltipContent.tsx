import { useMemo } from 'react';
import * as RechartsPrimitive from 'recharts';
import { VariantProps, tv } from 'tailwind-variants';

import useChart from './hooks/useChart';
import getPayloadConfigFromPayload from './utils/getPayloadConfigFromPayload';

export const chartTooltipContentStyles = tv({
  slots: {
    root: 'border-border-primary/50 bg-background-primary grid min-w-[8rem] items-start gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs shadow-xl',
    label: 'font-medium',
    indicator:
      '[&>svg]:text-text-muted flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5',
    indicatorDot:
      'shrink-0 rounded-[2px] border-[--color-border] bg-[--color-bg]',
    row: 'flex flex-1 justify-between leading-none',
    labelContainer: 'grid gap-1.5',
    valueText: 'text-text-primary font-mono font-medium tabular-nums'
  },
  variants: {
    indicator: {
      dot: {
        indicator: 'items-center',
        indicatorDot: 'h-2.5 w-2.5'
      },
      line: {
        indicatorDot: 'w-1'
      },
      dashed: {
        indicatorDot: 'w-0 border-[1.5px] border-dashed bg-transparent'
      }
    },
    nestLabel: {
      true: {
        row: 'items-end'
      },
      false: {
        row: 'items-center'
      }
    }
  },
  compoundVariants: [
    {
      indicator: 'dashed',
      nestLabel: true,
      class: {
        indicatorDot: 'my-0.5'
      }
    }
  ],
  defaultVariants: {
    indicator: 'dot',
    nestLabel: false
  }
});

export interface ChartTooltipContentProps
  extends React.ComponentProps<typeof RechartsPrimitive.Tooltip>,
    VariantProps<typeof chartTooltipContentStyles> {
  hideLabel?: boolean;
  hideIndicator?: boolean;
  indicator?: 'line' | 'dot' | 'dashed';
  nameKey?: string;
  labelKey?: string;
  className?: string;
  color?: string;
}

const {
  root: rootStyles,
  label: labelStyles,
  indicator: indicatorStyles,
  indicatorDot: indicatorDotStyles,
  row: rowStyles,
  labelContainer: labelContainerStyles,
  valueText: valueTextStyles
} = chartTooltipContentStyles();

const ChartTooltipContent = ({
  active,
  payload,
  className,
  indicator = 'dot',
  hideLabel = false,
  hideIndicator = false,
  label,
  labelFormatter,
  labelClassName,
  formatter,
  color,
  nameKey,
  labelKey
}: ChartTooltipContentProps) => {
  const { config } = useChart();

  const tooltipLabel = useMemo(() => {
    if (hideLabel || !payload?.length) {
      return null;
    }

    const [item] = payload;
    const key = `${labelKey || item?.dataKey || item?.name || 'value'}`;
    const itemConfig = getPayloadConfigFromPayload(config, item, key);
    const value =
      !labelKey && typeof label === 'string'
        ? config[label as keyof typeof config]?.label || label
        : itemConfig?.label;

    if (labelFormatter) {
      return (
        <div className={labelStyles({ className: labelClassName })}>
          {labelFormatter(value, payload)}
        </div>
      );
    }

    if (!value) {
      return null;
    }

    return (
      <div className={labelStyles({ className: labelClassName })}>{value}</div>
    );
  }, [
    label,
    labelFormatter,
    payload,
    hideLabel,
    labelClassName,
    config,
    labelKey
  ]);

  if (!active || !payload?.length) {
    return null;
  }

  const nestLabel = payload.length === 1 && indicator !== 'dot';

  return (
    <div className={rootStyles({ className })}>
      {!nestLabel ? tooltipLabel : null}
      <div className="grid gap-1.5">
        {payload.map((item, index) => {
          const key = `${nameKey || item.name || item.dataKey || 'value'}`;
          const itemConfig = getPayloadConfigFromPayload(config, item, key);
          const indicatorColor = color || item.payload.fill || item.color;

          return (
            <div key={item.dataKey} className={indicatorStyles({ indicator })}>
              {formatter && item?.value !== undefined && item.name ? (
                formatter(item.value, item.name, item, index, item.payload)
              ) : (
                <>
                  {itemConfig?.icon ? (
                    <itemConfig.icon />
                  ) : (
                    !hideIndicator && (
                      <div
                        className={indicatorDotStyles({ indicator, nestLabel })}
                        style={
                          {
                            '--color-bg': indicatorColor,
                            '--color-border': indicatorColor
                          } as React.CSSProperties
                        }
                      />
                    )
                  )}
                  <div className={rowStyles({ nestLabel })}>
                    <div className={labelContainerStyles()}>
                      {nestLabel ? tooltipLabel : null}
                      <span className="text-text-muted">
                        {itemConfig?.label || item.name}
                      </span>
                    </div>
                    {item.value && (
                      <span className={valueTextStyles()}>
                        {item.value.toLocaleString()}
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ChartTooltipContent;
