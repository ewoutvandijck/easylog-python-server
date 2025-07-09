import { VariantProps, tv } from 'tailwind-variants';

export const tableBodyStyles = tv({
  base: '[&_tr:last-child]:border-0'
});

export interface TableBodyProps
  extends React.HTMLAttributes<HTMLTableSectionElement>,
    VariantProps<typeof tableBodyStyles> {}

const TableBody = ({ className, ...props }: TableBodyProps) => {
  return <tbody className={tableBodyStyles({ className })} {...props} />;
};

export default TableBody;
