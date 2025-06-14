import { IconChevronDown } from '@tabler/icons-react';
import React from 'react';
import { VariantProps, tv } from 'tailwind-variants';

import useComboboxContext from './useComboboxContext';
import ContentWrapper, {
  ContentWrapperProps
} from '../ContentWrapper/ContentWrapper';

const comboboxTriggerContentStyles = tv({
  variants: {
    isActive: {
      true: '',
      false: 'font-normal text-text-muted'
    }
  },
  defaultVariants: {
    isActive: false
  }
});
export interface ComboboxTriggerContentProps
  extends Omit<ContentWrapperProps, 'iconRight'>,
    VariantProps<typeof comboboxTriggerContentStyles> {
  placeholder?: React.ReactNode;
}

const ComboBoxTriggerContent = ({
  className,
  placeholder,
  children,
  ...props
}: React.PropsWithChildren<ComboboxTriggerContentProps>) => {
  const { activeItem } = useComboboxContext();

  return (
    <ContentWrapper
      {...props}
      align="start"
      iconRight={IconChevronDown}
      className={comboboxTriggerContentStyles({
        isActive: !!activeItem,
        className
      })}
    >
      {activeItem !== null ? children : placeholder}
    </ContentWrapper>
  );
};

export default ComboBoxTriggerContent;
