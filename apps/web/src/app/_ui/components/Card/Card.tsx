import { Slot } from '@radix-ui/react-slot';
import { VariantProps, tv } from 'tailwind-variants';

export const cardStyles = tv({
  base: 'relative overflow-hidden rounded-lg',
  variants: {
    colorRole: {
      primary: 'border-border-primary bg-surface-primary',
      muted: 'border-border-muted bg-surface-muted',
      tertiary: 'border-border-tertiary bg-surface-tertiary',
      brand: 'text-text-brand-on-fill border-border-brand bg-fill-brand'
    },
    variant: {
      ghost: null,
      outline: 'border border-b-2'
    },
    shadow: {
      none: null,
      sm: 'shadow-xs'
    }
  },
  defaultVariants: {
    colorRole: 'primary',
    variant: 'outline',
    shadow: 'sm'
  }
});

export interface CardProps
  extends VariantProps<typeof cardStyles>,
    React.HTMLAttributes<HTMLDivElement> {
  asChild?: boolean;
}

const Card = ({
  colorRole,
  variant,
  shadow,
  className,
  children,
  asChild,
  ...props
}: React.PropsWithChildren<CardProps>) => {
  const Component = asChild ? Slot : 'article';

  return (
    <Component
      className={cardStyles({ colorRole, variant, className, shadow })}
      {...props}
    >
      {children}
    </Component>
  );
};

export default Card;
