'use client';

import { VariantProps, tv } from 'tailwind-variants';

import useNavigationMenuContext from '@/app/_ui/hooks/useNavigationMenuContext';

const navigationMenuStyles = tv({
  slots: {
    rootWrapper: 'relative flex gap-1',
    itemsWrapper: 'relative flex',
    hoverElement:
      'pointer-events-none absolute left-0 top-0 z-0 h-full rounded-lg bg-fill-muted transition-all',
    activeElement:
      'absolute left-0 z-20 rounded-full bg-text-primary transition-all'
  },
  variants: {
    direction: {
      vertical: {
        rootWrapper: 'flex-col px-1',
        itemsWrapper: 'group/nav flex-col',
        activeElement: 'left-0 w-0.5'
      },
      horizontal: {
        rootWrapper: 'flex-row py-1',
        itemsWrapper: 'flex-row',
        activeElement: 'bottom-0 h-0.5'
      }
    }
  },
  defaultVariants: {
    direction: 'horizontal',
    hasSelectedElement: false
  }
});

const {
  rootWrapper,
  itemsWrapper,
  hoverElement: hoverElementStyles,
  activeElement: activeElementStyles
} = navigationMenuStyles();

export interface NavigationMenuProps
  extends VariantProps<typeof navigationMenuStyles> {
  className?: string;
  hideUnderline?: boolean;
}

const NavigationMenu = ({
  direction,
  className,
  hideUnderline = false,
  children
}: React.PropsWithChildren<NavigationMenuProps>) => {
  const { hoverElement, selectedElement } = useNavigationMenuContext();

  return (
    <div className={rootWrapper({ direction, className })}>
      <nav className={itemsWrapper({ direction })} data-dir={direction}>
        <div
          className={hoverElementStyles({ direction })}
          style={
            hoverElement
              ? {
                  transform: `translateX(${hoverElement.offsetLeft}px) translateY(${hoverElement.offsetTop}px)`,
                  width: hoverElement.offsetWidth,
                  opacity: 1,
                  scale: 1
                }
              : selectedElement
                ? {
                    transform: `translateX(${selectedElement.offsetLeft}px) translateY(${selectedElement.offsetTop}px)`,
                    width: selectedElement.offsetWidth,
                    opacity: 1,
                    scale: 1
                  }
                : {
                    scale: 0,
                    opacity: 0
                  }
          }
        />

        {children}
      </nav>
      {!hideUnderline && (
        <div
          className={activeElementStyles({
            direction
          })}
          style={
            selectedElement
              ? {
                  opacity: 1,
                  ...(direction === 'vertical'
                    ? {
                        height: selectedElement.offsetHeight,
                        transform: `translateY(${selectedElement.offsetTop}px) translateX(-0.5px)`
                      }
                    : {
                        width: selectedElement.offsetWidth,
                        transform: `translateX(${selectedElement.offsetLeft}px) translateY(0.5px)`
                      })
                }
              : {
                  transform: `translateX(${hoverElement?.offsetLeft ?? 0}px) translateY(${hoverElement?.offsetTop ?? 0}px)`,
                  opacity: 0,
                  scale: 0
                }
          }
        />
      )}
    </div>
  );
};

export default NavigationMenu;
