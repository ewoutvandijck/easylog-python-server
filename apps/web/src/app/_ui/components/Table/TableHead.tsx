import { VariantProps, tv } from 'tailwind-variants';

import Typography from '../Typography/Typography';

export const tableHeadStyles = tv({
  base: 'h-12 border-b border-border-muted px-1.5 text-left align-middle first:pl-3.5 last:pr-3.5 [&:has([role=checkbox])]:pr-0'
});

export interface TableHeadProps
  extends React.ThHTMLAttributes<HTMLTableCellElement>,
    VariantProps<typeof tableHeadStyles> {}

const TableHead = ({ className, ...props }: TableHeadProps) => {
  return (
    <Typography variant="bodySm" colorRole="muted" asChild>
      <th className={tableHeadStyles({ className })} {...props} />
    </Typography>
  );
};

export default TableHead;
