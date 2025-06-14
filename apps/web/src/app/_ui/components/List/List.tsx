import { VariantProps, tv } from 'tailwind-variants';

export const listStyles = tv({
  base: 'shadow-xs rounded-xl'
});

export interface ListProps
  extends VariantProps<typeof listStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const List = ({ className, ...props }: ListProps) => {
  return <div className={listStyles({ className })} {...props} />;
};

export default List;
