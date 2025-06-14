import Typography, { TypographyProps } from '../Typography/Typography';

export interface CardTitleProps extends TypographyProps {}

const CardTitle = ({
  children,
  ...props
}: React.PropsWithChildren<CardTitleProps>) => {
  return (
    <Typography asChild variant="headingSm" {...props}>
      <h3>{children}</h3>
    </Typography>
  );
};

export default CardTitle;
