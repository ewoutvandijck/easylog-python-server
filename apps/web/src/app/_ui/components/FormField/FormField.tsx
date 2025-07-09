import { Slot } from '@radix-ui/react-slot';
import { VariantProps, tv } from 'tailwind-variants';

const formFieldStyles = tv({
  base: 'flex max-w-full flex-1 flex-col space-y-2'
});

export interface FormFieldProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof formFieldStyles> {
  asChild?: boolean;
}

const FormField = ({ className, asChild, ...props }: FormFieldProps) => {
  const Comp = asChild ? Slot : 'div';
  return <Comp className={formFieldStyles({ className })} {...props} />;
};

export default FormField;
