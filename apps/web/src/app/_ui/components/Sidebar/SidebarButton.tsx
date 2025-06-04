import { Slot } from '@radix-ui/react-slot';
import { type VariantProps, tv } from 'tailwind-variants';

export const sidebarButtonStyles = tv({
  base: 'ring-border-primary-selected focus:outline-hidden hover:bg-fill-primary-hover active:bg-fill-primary-active data-[state=open]:bg-fill-primary-selected data-[state=open]:hover:bg-fill-primary-hover data-[state=open]:active:bg-fill-primary-active box-border flex shrink-0 items-center rounded-lg bg-transparent text-sm outline-none transition-all duration-150 focus-visible:ring-2',
  variants: {
    size: {
      xs: 'h-7 px-1.5',
      sm: 'h-8 px-2',
      md: 'h-9 px-2.5',
      lg: 'h-10 px-3',
      xl: 'text-md h-12 px-4'
    },
    isDisabled: {
      true: 'pointer-events-none cursor-not-allowed opacity-50',
      false: null
    }
  },

  defaultVariants: {
    size: 'md'
  }
});

export interface SidebarButtonProps
  extends VariantProps<typeof sidebarButtonStyles> {
  asChild?: boolean;
  isToggled?: boolean;
}

const SidebarButton = ({
  size,
  asChild,
  className,
  children,
  isDisabled,
  isToggled,
  ...props
}: React.PropsWithChildren<
  SidebarButtonProps & React.ButtonHTMLAttributes<HTMLButtonElement>
>) => {
  const Component = asChild ? Slot : 'button';

  return (
    <Component
      aria-disabled={isDisabled}
      data-state={isToggled ? 'open' : undefined}
      className={sidebarButtonStyles({
        isDisabled,
        size,
        className
      })}
      {...props}
    >
      {children}
    </Component>
  );
};

export default SidebarButton;
