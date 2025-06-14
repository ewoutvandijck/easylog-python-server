import { forwardRef } from 'react';
import { VariantProps, tv } from 'tailwind-variants';

import Typography from '../Typography/Typography';

export const fieldsetStyles = tv({
  slots: {
    wrapper: 'space-y-2'
  }
});

export interface FieldsetProps extends VariantProps<typeof fieldsetStyles> {
  label?: React.ReactNode;
}

const { wrapper } = fieldsetStyles();

const Fieldset = forwardRef<
  HTMLFieldSetElement,
  FieldsetProps & React.FieldsetHTMLAttributes<HTMLFieldSetElement>
>(({ label, className, children, ...props }, ref) => {
  return (
    <fieldset ref={ref} className={wrapper({ className })} {...props}>
      {label && (
        <Typography variant="labelMd" asChild>
          <legend>{label}</legend>
        </Typography>
      )}
      {children}
    </fieldset>
  );
});

Fieldset.displayName = 'Fieldset';

export default Fieldset;
