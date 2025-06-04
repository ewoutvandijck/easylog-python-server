import { VariantProps, tv } from 'tailwind-variants';

export const tableHeaderStyles = tv({
  base: 'relative z-10 border-border-primary bg-surface-primary [&_tr]:border-b'
});

export interface TableHeaderProps
  extends React.HTMLAttributes<HTMLTableSectionElement>,
    VariantProps<typeof tableHeaderStyles> {}

const TableHeader = ({ className, ...props }: TableHeaderProps) => {
  return <thead className={tableHeaderStyles({ className })} {...props} />;
};

export default TableHeader;
