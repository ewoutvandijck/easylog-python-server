import { Slot } from '@radix-ui/react-slot';
import { VariantProps, tv } from 'tailwind-variants';

const formFieldContentStyles = tv({
  base: 'flex flex-1 gap-x-2 gap-y-1',
  variants: {
    direction: {
      vertical: 'flex-col',
      horizontal: 'flex-row items-center'
    }
  },
  defaultVariants: {
    direction: 'vertical'
  }
});

export interface FormFieldContentProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof formFieldContentStyles> {
  asChild?: boolean;
}

const FormFieldContent = ({
  className,
  direction,
  asChild,
  ...props
}: FormFieldContentProps) => {
  const Comp = asChild ? Slot : 'div';
  return (
    <Comp
      className={formFieldContentStyles({ className, direction })}
      {...props}
    />
  );
};

export default FormFieldContent;
