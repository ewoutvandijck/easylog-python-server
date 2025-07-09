import { VariantProps, tv } from 'tailwind-variants';

export const badgeStyles = tv({
  base: 'focus:outline-hidden focus:ring-border-primary inline-flex items-center rounded-full border text-xs transition-colors focus:ring-2 focus:ring-offset-2',
  variants: {
    colorRole: {
      primary: 'border-border-primary bg-fill-primary',
      muted: 'border-border-muted bg-fill-muted',
      brand: 'bg-fill-brand/10 text-text-brand border-transparent',
      danger: 'bg-fill-danger/10 text-text-danger border-transparent',
      warning: 'bg-fill-warning/10 text-text-warning border-transparent'
    },
    size: {
      xs: 'h-6 px-1.5',
      sm: 'h-7 px-2',
      md: 'h-8 px-2.5'
    }
  },
  defaultVariants: {
    colorRole: 'primary',
    size: 'md'
  }
});

export interface BadgeProps
  extends React.HtmlHTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeStyles> {}

const Badge = ({ className, colorRole, size, ...props }: BadgeProps) => {
  return (
    <span className={badgeStyles({ className, colorRole, size })} {...props} />
  );
};

export default Badge;
