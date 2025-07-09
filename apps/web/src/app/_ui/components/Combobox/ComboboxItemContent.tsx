import { IconCheck } from '@tabler/icons-react';

import useComboboxContext from './useComboboxContext';
import ContentWrapper, {
  ContentWrapperProps
} from '../ContentWrapper/ContentWrapper';

export interface ComboboxItemContentProps extends ContentWrapperProps {
  value: string;
}

const ComboBoxItemContent = ({
  children,
  value,
  iconRight,
  ...props
}: React.PropsWithChildren<ComboboxItemContentProps>) => {
  const { activeItem } = useComboboxContext();

  return (
    <ContentWrapper
      {...props}
      align="start"
      iconRight={value === activeItem?.id.toString() ? IconCheck : iconRight}
    >
      {children}
    </ContentWrapper>
  );
};

export default ComboBoxItemContent;
