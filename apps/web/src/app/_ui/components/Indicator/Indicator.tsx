import { VariantProps, tv } from 'tailwind-variants';

import Typography from '../Typography/Typography';

const indicatorStyles = tv({
  base: 'flex items-center justify-center rounded-lg',
  variants: {
    size: {
      sm: 'size-4',
      md: 'size-5',
      lg: 'size-6'
    },
    colorRole: {
      primary: 'text-text-primary-on-fill bg-fill-primary',
      brand: 'text-text-brand-on-fill bg-fill-brand'
    }
  },
  defaultVariants: {
    size: 'md',
    colorRole: 'brand'
  }
});

export interface IndicatorProps extends VariantProps<typeof indicatorStyles> {
  className?: string;
}

const Indicator = ({
  size,
  colorRole,
  className,
  ...props
}: React.PropsWithChildren<IndicatorProps>) => {
  return (
    <Typography asChild variant="labelXs">
      <span
        {...props}
        className={indicatorStyles({ size, colorRole, className })}
      />
    </Typography>
  );
};

export default Indicator;
