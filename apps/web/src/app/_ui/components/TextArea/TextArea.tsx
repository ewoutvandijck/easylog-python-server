import { Slot } from '@radix-ui/react-slot';
import { type VariantProps, tv } from 'tailwind-variants';

import Icon, { type IconProp } from '../Icon/Icon';

export const textAreaStyles = tv({
  slots: {
    root: 'box-border flex flex-shrink-0 items-center font-sans text-sm ring-2 ring-transparent transition-all dark:bg-white/10',
    input:
      'placeholder:text-text-secondary/75 text-text-primary block max-w-full grow border-none bg-transparent text-sm focus:outline-none'
  },
  variants: {
    variant: {
      outline: {
        root: '[&:not([data-state=disabled])]:hover:border-border-primary-hover border-border-primary bg-fill-primary focus-within:ring-border-primary border'
      },
      ghost: null
    },
    size: {
      sm: {
        root: 'min-h-8 rounded-md',
        input: 'min-h-8 px-2 py-1.5'
      },
      md: {
        root: 'min-h-9',
        input: 'min-h-9 px-2.5 py-2'
      },
      lg: {
        root: 'text-md min-h-10',
        input: 'min-h-10 px-3.5 py-2.5'
      }
    },
    shape: {
      rounded: {
        root: 'rounded-lg'
      },
      pill: {
        root: 'rounded-full'
      }
    },
    isDisabled: {
      true: {
        input: 'pointer-events-none cursor-not-allowed opacity-50'
      }
    },
    isTransparent: {
      true: {
        root: 'bg-transparent'
      }
    },
    hasIconLeft: {
      true: {
        root: 'pl-2.5'
      }
    }
  },
  defaultVariants: {
    size: 'md',
    variant: 'outline',
    isTransparent: false,
    shape: 'rounded'
  }
});

export interface TextAreaProps
  extends Omit<
      React.TextareaHTMLAttributes<HTMLTextAreaElement>,
      'size' | 'size'
    >,
    VariantProps<typeof textAreaStyles> {
  asChild?: boolean;
  iconLeft?: IconProp;
  iconRight?: IconProp;
  contentLeft?: React.ReactNode;
  contentRight?: React.ReactNode;
}

const { root, input } = textAreaStyles();

const TextArea = ({
  className,
  asChild,
  variant,
  size,
  iconLeft,
  iconRight,
  contentLeft,
  contentRight,
  isDisabled,
  isTransparent,
  shape,
  ...props
}: TextAreaProps) => {
  const Comp = asChild ? Slot : 'textarea';

  const hasIconLeft = !!iconLeft || !!contentLeft;

  return (
    <div
      data-state={isDisabled ? 'disabled' : 'enabled'}
      className={root({
        variant,
        size,
        isDisabled,
        isTransparent,
        shape,
        className,
        hasIconLeft
      })}
    >
      <span className="block">
        {iconLeft && <Icon icon={iconLeft} />}
        {contentLeft}
      </span>
      <Comp
        className={input({ size, isDisabled, hasIconLeft })}
        {...props}
        aria-disabled={isDisabled}
        disabled={isDisabled}
      />
      <span>
        {iconRight && <Icon icon={iconRight} />}
        {contentRight}
      </span>
    </div>
  );
};

export default TextArea;
