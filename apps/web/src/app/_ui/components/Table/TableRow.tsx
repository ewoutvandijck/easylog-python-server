import { VariantProps, tv } from 'tailwind-variants';

export const tableRowStyles = tv({
  base: 'transition-colors',
  variants: {
    isHeaderRow: {
      false:
        'hover:bg-surface-primary-hover data-[state=selected]:bg-surface-primary-selected'
    }
  },
  defaultVariants: {
    isHeaderRow: false
  }
});

export interface TableRowProps
  extends React.HTMLAttributes<HTMLTableRowElement>,
    VariantProps<typeof tableRowStyles> {}

const TableRow = ({ className, isHeaderRow, ...props }: TableRowProps) => {
  return (
    <tr className={tableRowStyles({ className, isHeaderRow })} {...props} />
  );
};

export default TableRow;
