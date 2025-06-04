import { VariantProps, tv } from 'tailwind-variants';

import Skeleton, { SkeletonProps } from '../Skeleton/Skeleton';

export const buttonSkeletonStyles = tv({
  variants: {
    size: {
      sm: 'min-h-8',
      md: 'min-h-9',
      lg: 'min-h-10'
    },
    shape: {
      rect: 'rounded-lg',
      circle: 'rounded-full'
    },
    compoundVariants: [
      {
        shape: 'circle',
        size: 'sm',
        class: 'w-8 p-1'
      },
      {
        shape: 'circle',
        size: 'md',
        class: 'w-9 p-1'
      },
      {
        shape: 'circle',
        size: 'lg',
        class: 'w-10 p-2'
      }
    ]
  },
  defaultVariants: {
    size: 'md',
    shape: 'rect'
  }
});

export interface ButtonSkeletonProps
  extends VariantProps<typeof buttonSkeletonStyles>,
    SkeletonProps {}

const ButtonSkeleton = ({
  className,
  size,
  shape,
  ...props
}: ButtonSkeletonProps) => {
  return (
    <Skeleton
      className={buttonSkeletonStyles({ size, shape, className })}
      {...props}
    />
  );
};

export default ButtonSkeleton;
