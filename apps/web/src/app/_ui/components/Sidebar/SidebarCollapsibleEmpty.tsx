import { VariantProps, tv } from 'tailwind-variants';

import Typography, { TypographyProps } from '../Typography/Typography';

export const sidebarCollapsibleEmptyStyles = tv({
  base: 'ml-8 max-w-full truncate'
});

export interface SidebarCollapsibleEmptyProps
  extends TypographyProps,
    VariantProps<typeof sidebarCollapsibleEmptyStyles> {}

const SidebarCollapsibleEmpty = ({
  className,
  children,
  ...props
}: React.PropsWithChildren<SidebarCollapsibleEmptyProps>) => {
  return (
    <Typography
      variant="bodyXs"
      colorRole="muted"
      className={sidebarCollapsibleEmptyStyles({ className })}
      {...props}
    >
      {children}
    </Typography>
  );
};

export default SidebarCollapsibleEmpty;
