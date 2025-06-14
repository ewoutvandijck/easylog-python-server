import { VariantProps, tv } from 'tailwind-variants';

const stepsStyles = tv({
  base: 'flex flex-row gap-2'
});

export interface StepsProps extends VariantProps<typeof stepsStyles> {
  className?: string;
}

const Steps = ({
  className,
  children,
  ...props
}: React.PropsWithChildren<StepsProps>) => {
  return (
    <div className={stepsStyles({ className })} {...props}>
      {children}
    </div>
  );
};

export default Steps;
