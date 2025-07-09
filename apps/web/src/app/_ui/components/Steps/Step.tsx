import { VariantProps, tv } from 'tailwind-variants';

const stepStyles = tv({
  base: 'h-1 grow rounded-lg',
  variants: {
    isActive: {
      true: 'bg-fill-brand',
      false: 'bg-fill-muted'
    }
  },
  defaultVariants: {
    isActive: false
  }
});

export interface StepProps extends VariantProps<typeof stepStyles> {
  className?: string;
}

const Step = ({
  isActive,
  className,
  children,
  ...props
}: React.PropsWithChildren<StepProps>) => {
  return (
    <div className={stepStyles({ isActive, className })} {...props}>
      {children}
    </div>
  );
};

export default Step;
