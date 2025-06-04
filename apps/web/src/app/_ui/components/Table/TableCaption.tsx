import { VariantProps, tv } from 'tailwind-variants';

export const tableCaptionStyles = tv({
  base: 'mt-4 text-sm text-text-muted'
});

export interface TableCaptionProps
  extends React.HTMLAttributes<HTMLTableCaptionElement>,
    VariantProps<typeof tableCaptionStyles> {}

const TableCaption = ({ className, ...props }: TableCaptionProps) => {
  return <caption className={tableCaptionStyles({ className })} {...props} />;
};

export default TableCaption;
