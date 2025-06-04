import { Slot } from '@radix-ui/react-slot';
import { VariantProps, tv } from 'tailwind-variants';

import Typography, { TypographyProps } from '../Typography/Typography';

const formFieldLabelStyles = tv({
  base: 'cursor-pointer',
  variants: {
    isDisabled: {
      true: 'cursor-not-allowed text-text-muted'
    }
  }
});

export interface FormFieldLabelProps
  extends React.HTMLAttributes<HTMLLabelElement>,
    VariantProps<typeof formFieldLabelStyles>,
    TypographyProps {
  asChild?: boolean;
}

const FormFieldLabel = ({
  className,
  isDisabled,
  asChild,
  children,
  ...props
}: React.PropsWithChildren<FormFieldLabelProps>) => {
  const Comp = asChild ? Slot : 'label';
  return (
    <Typography
      variant="labelSm"
      className={formFieldLabelStyles({ className, isDisabled })}
      asChild
      {...props}
    >
      <Comp>{children}</Comp>
    </Typography>
  );
};

export default FormFieldLabel;
