'use client';

import { useTheme } from 'next-themes';
import { Toaster as Sonner } from 'sonner';

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme, forcedTheme } = useTheme();

  return (
    <Sonner
      theme={(forcedTheme ?? theme) as ToasterProps['theme']}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            'group toast group-[.toaster]:bg-surface-primary group-[.toaster]:text-text-primary group-[.toaster]:border-border-primary group-[.toaster]:shadow-xs',
          description: 'group-[.toast]:text-text-muted',
          actionButton:
            'group-[.toast]:bg-fill-primary group-[.toast]:text-text-primary',
          cancelButton:
            'group-[.toast]:bg-fill-primary group-[.toast]:text-text-primary'
        }
      }}
      {...props}
    />
  );
};

export default Toaster;
