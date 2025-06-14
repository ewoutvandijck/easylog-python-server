import { Slot } from '@radix-ui/react-slot';
import { VariantProps, tv } from 'tailwind-variants';

import Typography, { TypographyProps } from '../Typography/Typography';

const tagStyles = tv({
  base: 'flex rounded-full',
  variants: {
    colorRole: {
      primary: 'border-border-primary bg-fill-primary text-text-primary',
      muted: 'border-border-muted bg-fill-muted/25 text-text-primary',
      brand: 'text-text-brand-on-fill border-border-brand bg-fill-brand',
      success: 'border-border-success bg-fill-success/25 text-text-success',
      danger: 'border-border-danger bg-fill-danger/25 text-text-danger',
      warning:
        'text-text-warning-on-fill border-border-warning bg-fill-warning/25'
    },
    size: {
      sm: 'px-1.5',
      md: 'px-2 py-0.5',
      lg: 'px-2.5 py-1'
    },
    isElevated: {
      true: 'border'
    }
  },

  defaultVariants: {
    colorRole: 'primary',
    isElevated: false,
    size: 'md'
  }
});

export interface TagProps extends VariantProps<typeof tagStyles> {
  className?: string;
  asChild?: boolean;
  variant?: TypographyProps['variant'];
}

/** @deprecated Use `Badge` instead. */
const Tag = ({
  isElevated,
  colorRole,
  size,
  className,
  asChild,
  variant = 'bodySm',
  children,
  ...props
}: React.PropsWithChildren<TagProps>) => {
  const Comp = asChild ? Slot : 'span';
  return (
    <Typography asChild variant={variant}>
      <Comp
        {...props}
        className={tagStyles({ colorRole, size, isElevated, className })}
      >
        {children}
      </Comp>
    </Typography>
  );
};

export default Tag;
