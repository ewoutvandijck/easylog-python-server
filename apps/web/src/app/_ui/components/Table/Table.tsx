import { VariantProps, tv } from 'tailwind-variants';

export const tableStyles = tv({
  slots: {
    wrapper: 'w-full',
    table: 'w-full caption-bottom border-separate border-spacing-0 text-sm'
  }
});

export interface TableProps
  extends React.HTMLAttributes<HTMLTableElement>,
    VariantProps<typeof tableStyles> {}

const { table } = tableStyles();

const Table = ({ className, ...props }: TableProps) => {
  return <table className={table({ className })} {...props} />;
};

export default Table;
