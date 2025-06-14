import { VariantProps, tv } from 'tailwind-variants';

export const listItemStyles = tv({
  base: 'not-last:border-b border-x border-border-primary bg-surface-primary first:rounded-t-lg first:border-t last:rounded-b-lg last:border-b'
});

export interface ListItemProps
  extends VariantProps<typeof listItemStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const ListItem = ({ className, ...props }: ListItemProps) => {
  return <div className={listItemStyles({ className })} {...props} />;
};

export default ListItem;
