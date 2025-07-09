import { type VariantProps, tv } from 'tailwind-variants';

import Icon, { type IconProp } from '../Icon/Icon';
import IconSpinner from '../Icon/IconSpinner';

export const contentWrapperStyles = tv({
  slots: {
    wrapper: 'inline-flex grow items-center truncate',
    leftFiller: 'shrink grow basis-0',
    iconLeft: 'shrink-0',
    iconRight: 'flex shrink-0 grow basis-0 justify-end',
    childrenWrapper: 'truncate'
  },
  variants: {
    align: {
      start: { wrapper: 'justify-start' },
      center: { wrapper: 'justify-center' },
      end: { wrapper: 'justify-end' }
    },
    size: {
      xs: {
        iconLeft: 'mr-0.5',
        iconRight: 'ml-0.5'
      },
      sm: {
        iconLeft: 'mr-1.5',
        iconRight: 'ml-1.5'
      },
      md: {
        iconLeft: 'mr-2',
        iconRight: 'ml-2'
      },
      lg: {
        iconLeft: 'mr-2.5',
        iconRight: 'ml-2.5'
      }
    }
  },
  defaultVariants: {
    stretch: false,
    size: 'md',
    align: 'center'
  }
});

export interface ContentWrapperProps
  extends VariantProps<typeof contentWrapperStyles> {
  className?: string;
  isLoading?: boolean;
  iconLeft?: IconProp;
  contentLeft?: React.ReactNode;
  iconRight?: IconProp;
  contentRight?: React.ReactNode;
}

const {
  wrapper,
  childrenWrapper,
  leftFiller,
  iconLeft: iconLeftStyles,
  iconRight: iconRightStyles
} = contentWrapperStyles();

const ContentWrapper = ({
  size,
  align,
  isLoading,
  iconLeft,
  contentLeft,
  iconRight,
  contentRight,
  className,
  children
}: React.PropsWithChildren<ContentWrapperProps>) => {
  iconLeft = isLoading ? IconSpinner : iconLeft;

  return (
    <span className={wrapper({ className, align })}>
      {(iconRight || contentRight) && align !== 'start' && (
        <span className={leftFiller()} />
      )}

      {contentLeft && (
        <span
          className={iconLeftStyles({
            size
          })}
        >
          {contentLeft}
        </span>
      )}

      {iconLeft && (
        <Icon className={iconLeftStyles({ size })} icon={iconLeft} />
      )}

      <span className={childrenWrapper()}>{children}</span>

      {iconRight && (
        <span
          className={iconRightStyles({
            size
          })}
        >
          <Icon icon={iconRight} />
        </span>
      )}

      {contentRight && (
        <span className={iconRightStyles({ size })}>{contentRight}</span>
      )}
    </span>
  );
};

export default ContentWrapper;
