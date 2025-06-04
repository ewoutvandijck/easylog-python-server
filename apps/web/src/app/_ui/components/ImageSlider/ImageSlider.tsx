'use client';

import { Slot } from '@radix-ui/react-slot';
import { IconArrowLeft, IconArrowRight } from '@tabler/icons-react';
import { Children, useMemo, useState } from 'react';
import { useSwipeable } from 'react-swipeable';
import { VariantProps, tv } from 'tailwind-variants';

import useKeyboardShortcut from '../../hooks/useKeyboardShortcut';
import Button from '../Button/Button';
import ButtonContent from '../Button/ButtonContent';
import Icon from '../Icon/Icon';
import Typography from '../Typography/Typography';

const imageSliderStyles = tv({
  slots: {
    /**
     * Touch action none prevents parent elements from scrolling when this
     * component is dragged on mobile
     */
    container: 'group relative flex w-full overflow-hidden',
    image:
      'flex w-full shrink-0 items-center justify-center overflow-hidden transition-all duration-150',
    counter:
      'absolute bottom-4 right-4 z-10 flex items-center rounded-md bg-fill-primary bg-opacity-75 px-1.5 py-0.5 transition-opacity md:opacity-0 md:group-hover:opacity-100',
    dots: 'absolute bottom-4 left-1/2 z-10 flex w-min -translate-x-1/2 items-center transition-opacity md:opacity-0 md:group-hover:opacity-100',
    dot: 'overflow-hidden rounded-full bg-fill-primary opacity-50 transition-all duration-150',
    leftControl:
      'absolute left-4 top-1/2 z-10 -translate-y-1/2 scale-100 transition-opacity duration-75',
    rightControl:
      'absolute right-4 top-1/2 z-10 -translate-y-1/2 scale-100 transition-opacity duration-75'
  },
  variants: {
    showControls: {
      always: {
        leftControl: 'opacity-100',
        rightControl: 'opacity-100'
      },
      hover: {
        leftControl: 'opacity-0 md:group-hover:opacity-100',
        rightControl: 'opacity-0 md:group-hover:opacity-100'
      },
      never: {
        leftControl: 'scale-90 opacity-0',
        rightControl: 'scale-90 opacity-0'
      }
    },
    counterStyle: {
      dots: {
        counter: 'opacity-0 md:group-hover:opacity-100',
        dot: 'opacity-50'
      },
      numbers: {
        counter: 'opacity-100',
        dot: 'opacity-100'
      }
    },
    dotSize: {
      outsideRange: { dot: 'size-0' },
      insideRange: { dot: 'size-1' },
      active: { dot: 'size-1.5 opacity-100' }
    },
    isSwiping: {
      true: { container: 'touch-none' }
    }
  },
  defaultVariants: {
    showControls: 'hover',
    counterStyle: 'dots'
  }
});

export interface ImageSliderProps
  extends VariantProps<typeof imageSliderStyles> {
  className?: string;
  counterDotsMaxItems?: number;
  initialIndex?: number;
  keyboardNavigation?: boolean;
  onIndexChange?: (index: number) => void;
}

export const {
  container,
  image,
  counter,
  dots,
  dot,
  leftControl,
  rightControl
} = imageSliderStyles();

const ImageSlider = ({
  className,
  showControls = 'hover',
  counterStyle = 'dots',
  counterDotsMaxItems = 5,
  initialIndex = 0,
  keyboardNavigation = false,
  onIndexChange,
  children
}: React.PropsWithChildren<ImageSliderProps>) => {
  // eslint-disable-next-line react-compiler/react-compiler
  'use no memo';

  const maxIndex = Children.count(children) - 1;

  const [dragOffset, setDragOffset] = useState(0);
  const [currentIndex, setCurrentIndex] = useState(
    Math.min(initialIndex, maxIndex)
  );

  const handlers = useSwipeable({
    preventScrollOnSwipe: true,
    onSwiped: (eventData) => {
      if (eventData.dir === 'Left' && currentIndex < maxIndex) {
        setCurrentIndex(currentIndex + 1);
        onIndexChange?.(currentIndex + 1);
      } else if (eventData.dir === 'Right' && currentIndex > 0) {
        setCurrentIndex(currentIndex - 1);
        onIndexChange?.(currentIndex - 1);
      }
      setDragOffset(0);
    },
    onSwiping: (eventData) => {
      setDragOffset(eventData.deltaX);
    }
  });

  useKeyboardShortcut(['ArrowLeft'], () => {
    if (currentIndex > 0 && keyboardNavigation) {
      setCurrentIndex(currentIndex - 1);
      onIndexChange?.(currentIndex - 1);
    }
  });

  useKeyboardShortcut(['ArrowRight'], () => {
    if (currentIndex < maxIndex && keyboardNavigation) {
      setCurrentIndex(currentIndex + 1);
      onIndexChange?.(currentIndex + 1);
    }
  });

  /**
   * Calculate the left and right index of the dots to show when the
   * counterStyle is 'dots' where we always show the counterDotsMaxItems and the
   * current index is centered.
   */
  const [dotsLeftIndex, dotsRightIndex] = useMemo(() => {
    if (maxIndex < counterDotsMaxItems) {
      return [0, maxIndex];
    }

    /** Calculate half window size, considering odd number of max items */
    const halfWindow = Math.floor(counterDotsMaxItems / 2);

    /** When currentIndex is close to the start */
    if (currentIndex - halfWindow < 0) {
      return [0, counterDotsMaxItems - 1];
    }

    /** When currentIndex is close to the end */
    if (currentIndex + halfWindow > maxIndex) {
      return [maxIndex - (counterDotsMaxItems - 1), maxIndex];
    }

    /** Default case, center the current index */
    return [currentIndex - halfWindow, currentIndex + halfWindow];
  }, [counterDotsMaxItems, currentIndex, maxIndex]);

  const currentIndexOffsetPercentage = useMemo(
    () => `-${currentIndex * 100}%`,
    [currentIndex]
  );
  const dragOffsetPixels = useMemo(() => `${dragOffset}px`, [dragOffset]);

  return (
    <div
      className={container({
        // isSwiping: dragOffset !== 0,
        className
      })}
      {...handlers}
    >
      {/* Current image */}

      {counterStyle === 'numbers' && (
        <Typography asChild variant="bodySm">
          <span className={counter({ counterStyle })}>
            {currentIndex + 1} / {maxIndex + 1}
          </span>
        </Typography>
      )}

      {counterStyle === 'dots' && (
        <div className={dots({ counterStyle })}>
          {Array.from({ length: maxIndex + 1 }).map((_, index) => {
            const dotSize =
              index === currentIndex
                ? 'active'
                : index < dotsLeftIndex || index > dotsRightIndex
                  ? 'outsideRange'
                  : 'insideRange';

            return (
              <div
                key={`carousel-dot-${index}`}
                className={dot({
                  dotSize,
                  className:
                    index > 0 && dotSize !== 'outsideRange' ? 'ml-1' : undefined
                })}
              />
            );
          })}
        </div>
      )}

      {maxIndex > 0 && (
        <>
          {/* Controls */}
          <Button
            className={leftControl({
              showControls: currentIndex === 0 ? 'never' : showControls
            })}
            size="sm"
            shape="circle"
            isDisabled={currentIndex === 0}
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              setCurrentIndex(currentIndex - 1);
            }}
          >
            <ButtonContent size="sm">
              <Icon icon={IconArrowLeft} />
            </ButtonContent>
          </Button>

          <Button
            className={rightControl({
              showControls: currentIndex === maxIndex ? 'never' : showControls
            })}
            size="sm"
            shape="circle"
            isDisabled={currentIndex === maxIndex}
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              setCurrentIndex(currentIndex + 1);
            }}
          >
            <ButtonContent size="sm">
              <Icon icon={IconArrowRight} />
            </ButtonContent>
          </Button>
        </>
      )}

      {/* Images */}
      {Children.map(children, (child, index) => (
        <Slot
          key={`carousel-item-${index}`}
          style={{
            transform: `translate3d(calc(${currentIndexOffsetPercentage} + ${dragOffsetPixels}), 0, 0)`
          }}
          className={image()}
        >
          {child}
        </Slot>
      ))}
    </div>
  );
};

export default ImageSlider;
