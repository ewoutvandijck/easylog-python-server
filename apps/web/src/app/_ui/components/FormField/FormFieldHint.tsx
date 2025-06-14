import Typography, { TypographyProps } from '../Typography/Typography';

export interface FormFieldHintProps extends TypographyProps {}

const FormFieldHint = ({ ...props }: FormFieldHintProps) => {
  return <Typography variant="bodySm" colorRole="muted" {...props} />;
};

export default FormFieldHint;
