import { VariantProps, tv } from 'tailwind-variants';

import Typography from '../Typography/Typography';

export const tableCellStyles = tv({
  base: 'px-1.5 py-2.5 align-middle first:pl-3.5 last:pr-3.5'
});

export interface TableCellProps
  extends React.TdHTMLAttributes<HTMLTableCellElement>,
    VariantProps<typeof tableCellStyles> {}

const TableCell = ({ className, ...props }: TableCellProps) => {
  return (
    <Typography asChild variant="bodySm">
      <td className={tableCellStyles({ className })} {...props} />
    </Typography>
  );
};

export default TableCell;
