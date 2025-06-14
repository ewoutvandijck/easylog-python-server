'use client';

import { twMerge } from 'tailwind-merge';

import { useExpandable } from './hooks/useExpandable';

export interface ExpandableContentProps {
  className?: string;
}

const ExpandableContent = ({
  children,
  className
}: React.PropsWithChildren<ExpandableContentProps>) => {
  const { contentRef, totalContentRef, isExpanded } = useExpandable();

  return (
    <div className="relative overflow-hidden">
      <div
        ref={contentRef}
        className={twMerge('overflow-hidden', className)}
        data-expanded={isExpanded}
      >
        {children}
      </div>
      <div
        ref={totalContentRef}
        className="pointer-events-none absolute top-0 opacity-0"
        aria-hidden
        tabIndex={-1}
        data-expanded={isExpanded}
      >
        {children}
      </div>
    </div>
  );
};

export default ExpandableContent;
