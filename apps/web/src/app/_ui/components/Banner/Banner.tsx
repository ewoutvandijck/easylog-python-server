import { Slot } from '@radix-ui/react-slot';
import { VariantProps, tv } from 'tailwind-variants';

const bannerStyles = tv({
  base: 'rounded-lg',
  variants: {
    colorRole: {
      primary: 'bg-surface-primary text-text-primary',
      info: 'bg-surface-info text-text-info',
      muted: 'bg-surface-muted text-text-primary',
      success: 'bg-surface-success text-text-success',
      warning: 'text-text-warning-on-fill bg-surface-warning'
    },
    size: {
      sm: 'px-2.5 py-2',
      md: 'px-3 py-2.5 md:px-4 md:py-3',
      lg: 'px-4 py-3'
    }
  },
  defaultVariants: {
    colorRole: 'primary',
    size: 'md'
  }
});

export interface BannerProps extends VariantProps<typeof bannerStyles> {
  className?: string;
  asChild?: boolean;
}

const Banner = ({
  colorRole,
  size,
  className,
  children,
  asChild,
  ...props
}: React.PropsWithChildren<BannerProps>) => {
  const Comp = asChild ? Slot : 'div';

  return (
    <Comp {...props} className={bannerStyles({ colorRole, size, className })}>
      {children}
    </Comp>
  );
};

export default Banner;
