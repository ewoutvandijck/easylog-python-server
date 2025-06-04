import { VariantProps, tv } from 'tailwind-variants';

export const iconTypingStyles = tv({
  slots: {
    wrapper:
      'flex h-1/4 translate-y-1/4 items-center gap-0.5 transition-opacity',
    dotWrapper: 'flex h-full animate-bounce items-center duration-700',
    dot: 'size-1 rounded-full bg-text-muted'
  },
  variants: {
    isTyping: {
      true: {
        wrapper: 'opacity-100'
      },
      false: {
        wrapper: 'opacity-0'
      }
    }
  }
});

export interface IconTypingProps extends VariantProps<typeof iconTypingStyles> {
  className?: string;
}

const { wrapper, dotWrapper, dot } = iconTypingStyles();

const IconTyping = ({ isTyping, className }: IconTypingProps) => {
  return (
    <div className={wrapper({ className, isTyping })}>
      <div className={dotWrapper({ className: 'delay-0' })}>
        <div className={dot()} />
      </div>
      <div className={dotWrapper({ className: 'delay-150' })}>
        <div className={dot()} />
      </div>
      <div className={dotWrapper({ className: 'delay-300' })}>
        <div className={dot()} />
      </div>
    </div>
  );
};

export default IconTyping;
