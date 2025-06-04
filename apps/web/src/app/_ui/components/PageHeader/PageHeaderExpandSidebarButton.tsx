'use client';

import { IconLayoutSidebarLeftExpand } from '@tabler/icons-react';
import { tv } from 'tailwind-variants';

import Button from '@/app/_ui/components/Button/Button';
import Icon from '@/app/_ui/components/Icon/Icon';
import useSidebarContext from '@/app/_ui/components/Sidebar/hooks/useSidebarContext';

export const pageHeaderExpandSidebarButtonStyles = tv({
  base: '',
  variants: {
    isCollapsed: {
      true: 'block',
      false: 'md:hidden'
    }
  }
});

const PageHeaderExpandSidebarButton = () => {
  const { isCollapsed, setIsCollapsed } = useSidebarContext();

  return (
    <Button
      variant="ghost"
      shape="rect"
      size="sm"
      colorRole="muted"
      className={pageHeaderExpandSidebarButtonStyles({ isCollapsed })}
      onClick={() => setIsCollapsed(!isCollapsed)}
    >
      <Icon icon={IconLayoutSidebarLeftExpand} />
    </Button>
  );
};

export default PageHeaderExpandSidebarButton;
