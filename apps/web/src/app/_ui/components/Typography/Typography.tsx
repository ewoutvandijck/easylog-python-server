import { Slot } from '@radix-ui/react-slot';
import { type VariantProps, tv } from 'tailwind-variants';

export const typographyStyles = tv({
  variants: {
    variant: {
      monoXs: 'font-mono text-xs leading-4',
      monoSm: 'font-mono text-sm leading-5',
      monoMd: 'font-mono text-base leading-6',
      bodyXs: 'text-xs leading-4 tracking-[1%]',
      bodySm: 'text-sm leading-5 tracking-[1%]',
      bodyMd: 'text-base leading-6 tracking-[1%]',
      bodyLg: 'text-lg leading-7',
      bodyXl: 'text-xl leading-8',
      labelXs: 'text-xs font-medium leading-5',
      labelSm: 'text-sm font-medium leading-5',
      labelMd: 'text-base font-medium leading-6',
      labelLg: 'text-lg font-medium leading-7',
      labelXl: 'text-xl font-medium leading-8',
      headingXs: 'font-heading text-base font-medium leading-5 tracking-tight',
      headingSm: 'font-heading text-lg font-medium leading-6 tracking-tight',
      headingMd: 'font-heading text-xl font-medium leading-7 tracking-tight',
      headingLg: 'font-heading text-2xl font-medium leading-8 tracking-tight',
      displaySm: 'font-display md:leading-12 text-2xl leading-8 md:text-5xl',
      displayMd: 'font-display md:leading-13 text-3xl leading-9 md:text-6xl',
      displayLg: 'font-display md:leading-14 text-4xl leading-10 md:text-7xl',
      displayXl: 'font-display leading-12 md:leading-16 text-5xl md:text-8xl'
    },
    colorRole: {
      primary: 'text-text-primary',
      brand: 'text-text-brand',
      muted: 'text-text-muted',
      success: 'text-text-success',
      danger: 'text-text-danger',
      warning: 'text-text-warning'
    }
  },
  defaultVariants: {
    variant: 'bodyMd'
  }
});

export interface TypographyProps extends VariantProps<typeof typographyStyles> {
  className?: string;
  asChild?: boolean;
}

const Typography = ({
  variant,
  colorRole,
  className,
  asChild,
  children,
  ...props
}: React.PropsWithChildren<TypographyProps> &
  React.HTMLAttributes<
    HTMLParagraphElement | HTMLSpanElement | HTMLLabelElement
  >) => {
  const Comp = asChild ? Slot : 'p';
  return (
    <Comp
      className={typographyStyles({ variant, colorRole, className })}
      {...props}
    >
      {children}
    </Comp>
  );
};

export default Typography;
