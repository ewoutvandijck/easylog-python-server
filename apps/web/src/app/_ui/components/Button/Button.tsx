import { Slot } from '@radix-ui/react-slot';
import { type VariantProps, tv } from 'tailwind-variants';

export const buttonStyles = tv({
  base: 'focus:outline-hidden data-[state=open]:shadow-xs box-border flex shrink-0 items-center text-sm transition-all duration-150 focus-visible:ring-2',
  variants: {
    colorRole: {
      primary:
        'ring-border-primary-selected hover:border-border-primary-hover hover:bg-fill-primary-hover active:bg-fill-primary-active data-[state=open]:border-border-primary-selected data-[state=open]:bg-fill-primary-selected data-[state=open]:hover:border-border-primary-hover data-[state=open]:hover:bg-fill-primary-hover data-[state=open]:active:bg-fill-primary-active border-border-primary bg-fill-primary text-text-primary',
      muted:
        'ring-border-muted-selected hover:border-border-muted-hover hover:bg-fill-muted-hover active:bg-fill-muted-active data-[state=open]:border-border-muted-selected data-[state=open]:bg-fill-muted-selected data-[state=open]:hover:border-border-muted-hover data-[state=open]:hover:bg-fill-muted-hover data-[state=open]:active:bg-fill-muted-active border-border-muted bg-fill-muted text-text-muted',
      brand:
        'fill-text-brand-on-fill text-text-brand-on-fill ring-border-brand-selected hover:border-border-brand-hover hover:bg-fill-brand-hover active:bg-fill-brand-active data-[state=open]:border-border-brand-selected data-[state=open]:bg-fill-brand-selected data-[state=open]:hover:border-border-brand-hover data-[state=open]:hover:bg-fill-brand-hover data-[state=open]:active:bg-fill-brand-active border-border-brand bg-fill-brand',
      bold: 'border-border-bold ring-border-bold-selected hover:border-border-bold-hover data-[state=open]:border-border-bold-selected data-[state=open]:hover:border-border-bold-hover bg-fill-bold text-text-bold-on-fill hover:bg-fill-bold-hover active:bg-fill-bold-active data-[state=open]:bg-fill-bold-selected data-[state=open]:hover:bg-fill-bold-hover data-[state=open]:active:bg-fill-bold-active',
      danger:
        'text-text-danger-on-fill ring-border-danger-selected hover:border-border-danger-hover hover:bg-fill-danger-hover active:bg-fill-danger-active data-[state=open]:border-border-danger-selected data-[state=open]:bg-fill-danger-selected data-[state=open]:hover:border-border-danger-hover data-[state=open]:hover:bg-fill-danger-hover data-[state=open]:active:bg-fill-danger-active border-border-danger bg-fill-danger'
    },
    variant: {
      default: 'shadow-short data-[state=open]:shadow-none',
      ghost:
        'border-b-1 border-x border-t [&:not([data-state=open]):hover]:border-transparent [&:not([data-state=open]):not(:hover)]:border-transparent [&:not([data-state=open]):not(:hover)]:bg-transparent',
      outline: 'border'
    },
    size: {
      xs: 'h-7 px-1.5 text-xs',
      sm: 'h-8 px-2',
      md: 'h-9 px-2.5',
      lg: 'h-10 px-3',
      xl: 'text-md h-12 px-4'
    },
    shape: {
      rect: 'rounded-lg',
      circle: 'rounded-full',
      pill: 'rounded-full'
    },
    isDisabled: {
      true: 'pointer-events-none cursor-not-allowed opacity-50',
      false: null
    }
  },
  compoundVariants: [
    {
      shape: 'circle',
      size: 'xs',
      class: 'w-7 p-1'
    },
    {
      shape: 'circle',
      size: 'sm',
      class: 'w-8 p-1'
    },
    {
      shape: 'circle',
      size: 'md',
      class: 'w-9 p-1'
    },
    {
      shape: 'circle',
      size: 'lg',
      class: 'w-10 p-2'
    },
    {
      shape: 'circle',
      size: 'xl',
      class: 'w-12 p-4'
    }
  ],
  defaultVariants: {
    colorRole: 'primary',
    variant: 'default',
    size: 'md',
    shape: 'rect'
  }
});

export interface ButtonProps extends VariantProps<typeof buttonStyles> {
  asChild?: boolean;
  isToggled?: boolean;
}

const Button = ({
  colorRole,
  variant,
  size,
  asChild,
  shape,
  className,
  children,
  isDisabled,
  isToggled,
  ...props
}: React.PropsWithChildren<
  ButtonProps & React.ButtonHTMLAttributes<HTMLButtonElement>
>) => {
  const ButtonWrapper = asChild ? Slot : 'button';

  return (
    <ButtonWrapper
      aria-disabled={isDisabled}
      data-state={isToggled ? 'open' : undefined}
      className={buttonStyles({
        colorRole,
        variant,
        isDisabled,
        shape,
        size,
        className
      })}
      {...props}
    >
      {children}
    </ButtonWrapper>
  );
};

export default Button;
