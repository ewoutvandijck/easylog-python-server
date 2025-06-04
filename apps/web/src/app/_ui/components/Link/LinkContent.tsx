import { IconArrowUpRight } from '@tabler/icons-react';
import { VariantProps, tv } from 'tailwind-variants';

import ContentWrapper, {
  ContentWrapperProps
} from '../ContentWrapper/ContentWrapper';
import Icon from '../Icon/Icon';

export const linkContentStyles = tv({
  slots: {
    wrapper: 'group',
    icon: ''
  },
  variants: {
    hideIcon: {
      true: {
        icon: 'opacity-0 transition-opacity group-hover:opacity-100',
        wrapper: '-mr-5 transition-all hover:mr-0'
      },
      false: {
        icon: 'opacity-100',
        wrapper: ''
      }
    }
  },
  defaultVariants: {
    hideIcon: false
  }
});

export interface LinkContentProps
  extends ContentWrapperProps,
    VariantProps<typeof linkContentStyles> {
  isExternal?: boolean;
}

const { wrapper, icon } = linkContentStyles();

const LinkContent = ({
  children,
  isExternal = false,
  size = 'sm',
  hideIcon,
  className,
  contentRight,
  ...props
}: React.PropsWithChildren<LinkContentProps>) => {
  return (
    <ContentWrapper
      {...props}
      size={size}
      className={wrapper({
        hideIcon,
        className
      })}
      contentRight={
        isExternal ? (
          <Icon
            className={icon({
              hideIcon
            })}
            icon={IconArrowUpRight}
          />
        ) : (
          contentRight
        )
      }
    >
      {children}
    </ContentWrapper>
  );
};

export default LinkContent;
