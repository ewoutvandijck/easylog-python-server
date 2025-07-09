'use client';

import * as SliderPrimitive from '@radix-ui/react-slider';
import { useMemo } from 'react';
import { VariantProps, tv } from 'tailwind-variants';

export const sliderStyles = tv({
  slots: {
    root: 'relative my-2 flex w-full touch-none select-none items-center',
    track:
      'bg-fill-muted relative h-1 w-full grow overflow-hidden rounded-full',
    range: 'bg-text-primary dark:bg-border-primary absolute h-full',
    thumb:
      'border-border-primary bg-fill-primary dark:bg-text-primary ring-border-primary-hover/50 focus-visible:outline-hidden hover:border-border-primary-hover active:border-border-primary-active block size-6 rounded-full border shadow-sm transition-all hover:ring-2 focus-visible:ring-1 disabled:pointer-events-none disabled:opacity-50'
  }
});

export interface SliderProps
  extends React.ComponentProps<typeof SliderPrimitive.Root>,
    VariantProps<typeof sliderStyles> {
  min?: number;
  max?: number;
}

const { root, track, range, thumb } = sliderStyles();

const Slider = ({
  className,
  defaultValue,
  value,
  min = 0,
  max = 100,
  ...props
}: SliderProps) => {
  const _values = useMemo(
    () =>
      Array.isArray(value)
        ? value
        : Array.isArray(defaultValue)
          ? defaultValue
          : [min, max],
    [value, defaultValue, min, max]
  );

  return (
    <SliderPrimitive.Root
      className={root({ className })}
      defaultValue={defaultValue}
      value={value}
      min={min}
      max={max}
      {...props}
    >
      <SliderPrimitive.Track className={track()}>
        <SliderPrimitive.Range className={range()} />
      </SliderPrimitive.Track>
      {Array.from({ length: _values.length }, (_, index) => (
        <SliderPrimitive.Thumb key={index} className={thumb()} />
      ))}
    </SliderPrimitive.Root>
  );
};

export default Slider;
