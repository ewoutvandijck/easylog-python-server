import { Slot } from '@radix-ui/react-slot';
import { VariantProps, tv } from 'tailwind-variants';

export const sidebarMenuButtonStyles = tv({
  base: 'outline-hidden hover:bg-fill-muted-hover active:bg-fill-muted-active inline-flex items-center rounded-md bg-transparent px-2 text-sm transition-all duration-100',
  variants: {
    size: {
      sm: 'h-7',
      md: 'h-8',
      lg: 'h-9 text-base'
    },
    isActive: {
      true: 'bg-fill-muted-selected'
    }
  },
  defaultVariants: {
    size: 'md',
    isActive: false
  }
});

export interface SidebarMenuButtonProps
  extends React.HTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof sidebarMenuButtonStyles> {
  asChild?: boolean;
}

const SidebarMenuButton = ({
  asChild,
  size = 'md',
  isActive = false,
  className,
  children,
  ...props
}: SidebarMenuButtonProps) => {
  const T = asChild ? Slot : 'button';

  return (
    <T
      className={sidebarMenuButtonStyles({ size, className, isActive })}
      {...props}
    >
      {children}
    </T>
  );
};

export default SidebarMenuButton;
