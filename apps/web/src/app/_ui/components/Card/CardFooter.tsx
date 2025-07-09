import { VariantProps, tv } from 'tailwind-variants';

export const cardFooterStyles = tv({
  base: 'flex flex-row justify-between border-t border-border-primary',
  variants: {
    size: {
      md: 'px-6 py-3',
      lg: 'px-10 py-3'
    }
  },
  defaultVariants: {
    size: 'md'
  }
});

export interface CardFooterProps
  extends VariantProps<typeof cardFooterStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const CardFooter = ({
  size,
  className,
  children,
  ...props
}: React.PropsWithChildren<CardFooterProps>) => {
  return (
    <footer className={cardFooterStyles({ size, className })} {...props}>
      {children}
    </footer>
  );
};

export default CardFooter;
