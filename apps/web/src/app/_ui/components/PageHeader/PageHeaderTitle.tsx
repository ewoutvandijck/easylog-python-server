import Typography, {
  TypographyProps
} from '@/app/_ui/components/Typography/Typography';

const PageHeaderTitle = ({
  children,
  ...props
}: React.PropsWithChildren<TypographyProps>) => {
  return (
    <Typography asChild variant="labelMd" {...props}>
      <h1>{children}</h1>
    </Typography>
  );
};

export default PageHeaderTitle;
