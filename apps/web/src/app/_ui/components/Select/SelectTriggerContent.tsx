import * as SelectPrimitive from '@radix-ui/react-select';
import { IconChevronDown } from '@tabler/icons-react';
import { ComponentProps } from 'react';

import ContentWrapper, {
  ContentWrapperProps
} from '../ContentWrapper/ContentWrapper';
import Icon from '../Icon/Icon';
import IconSpinner from '../Icon/IconSpinner';
import Typography from '../Typography/Typography';

export interface SelectTriggerContentProps
  extends ComponentProps<typeof SelectPrimitive.Value> {
  contentLeft?: ContentWrapperProps['contentLeft'];
  size?: ContentWrapperProps['size'];
  isLoading?: boolean;
}

const SelectTriggerContent = ({
  contentLeft,
  children,
  size,
  isLoading,
  ...props
}: React.PropsWithChildren<SelectTriggerContentProps>) => {
  return (
    <ContentWrapper
      align="start"
      contentLeft={contentLeft}
      size={size}
      contentRight={
        isLoading ? (
          <Icon icon={IconSpinner} colorRole="muted" />
        ) : (
          <SelectPrimitive.Icon>
            <Icon icon={IconChevronDown} colorRole="muted" />
          </SelectPrimitive.Icon>
        )
      }
    >
      <Typography asChild variant="labelSm">
        <SelectPrimitive.Value {...props}>{children}</SelectPrimitive.Value>
      </Typography>
    </ContentWrapper>
  );
};

export default SelectTriggerContent;
