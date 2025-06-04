import Typography, { TypographyProps } from '../Typography/Typography';

export interface CardDescriptionProps extends TypographyProps {}

const CardDescription = ({
  children,
  ...props
}: React.PropsWithChildren<CardDescriptionProps>) => {
  return (
    <Typography asChild variant="bodySm" {...props}>
      <p>{children}</p>
    </Typography>
  );
};

export default CardDescription;
