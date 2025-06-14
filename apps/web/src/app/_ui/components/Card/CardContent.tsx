import { VariantProps, tv } from 'tailwind-variants';

export const cardContentStyles = tv({
  base: 'relative flex flex-col',
  variants: {
    size: {
      sm: 'gap-3 px-3 py-2',
      md: 'gap-6 p-6',
      lg: 'gap-8 p-8 md:px-10 md:py-9'
    }
  },
  defaultVariants: {
    size: 'md'
  }
});

export interface CardContentProps
  extends VariantProps<typeof cardContentStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const CardContent = ({
  size,
  className,
  children,
  ...props
}: React.PropsWithChildren<CardContentProps>) => {
  return (
    <div className={cardContentStyles({ size, className })} {...props}>
      {children}
    </div>
  );
};

export default CardContent;
