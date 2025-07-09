import { VariantProps, tv } from 'tailwind-variants';

export const dialogBodyStyles = tv({
  base: 'flex max-h-full grow flex-col gap-4 overflow-y-auto p-4'
});

export interface DialogBodyProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof dialogBodyStyles> {}

const DialogBody = ({ className, children, ...props }: DialogBodyProps) => {
  return (
    <div className={dialogBodyStyles({ className })} {...props}>
      {children}
    </div>
  );
};

export default DialogBody;
