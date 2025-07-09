import { type VariantProps, tv } from 'tailwind-variants';

export const dividerStyles = tv({
  slots: {
    wrapper: 'flex h-1 w-full items-center',
    line: 'h-px grow'
  },
  variants: {
    borderStyle: {
      solid: {
        line: 'border-solid'
      },
      dashed: {
        line: 'border-dashed'
      }
    },
    colorRole: {
      primary: {
        line: 'border-border-primary'
      },
      muted: {
        line: 'border-border-muted'
      }
    }
  },
  defaultVariants: {
    borderStyle: 'solid',
    colorRole: 'primary'
  }
});

export interface DividerProps extends VariantProps<typeof dividerStyles> {
  className?: string;
}

const { wrapper, line } = dividerStyles();

const Divider = ({
  className,
  colorRole,
  borderStyle,
  ...props
}: DividerProps) => {
  return (
    <div {...props} className={wrapper({ borderStyle, className })}>
      <hr className={line({ borderStyle, colorRole })} />
    </div>
  );
};

Divider.displayName = 'Divider';

export default Divider;
