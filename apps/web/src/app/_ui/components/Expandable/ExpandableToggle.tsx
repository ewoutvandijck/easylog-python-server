'use client';

import { Slot } from '@radix-ui/react-slot';

import { linkStyles } from '../Link/Link';
import Typography from '../Typography/Typography';
import { useExpandable } from './hooks/useExpandable';

export type ExpandableToggleProps = {
  asChild?: boolean;
  className?: string;
};

const ExpandableToggle = ({
  children,
  asChild,
  className
}: React.PropsWithChildren<ExpandableToggleProps>) => {
  const { toggleExpanded, isExpandable, isExpanded } = useExpandable();

  const Comp = asChild ? Slot : 'button';

  if (!isExpandable) return null;

  return (
    <Typography asChild variant="labelSm">
      <Comp
        onClick={toggleExpanded}
        className={linkStyles({ showUnderline: true, className })}
        data-expandable={isExpandable}
        data-expanded={isExpanded}
      >
        {children}
      </Comp>
    </Typography>
  );
};

export default ExpandableToggle;
