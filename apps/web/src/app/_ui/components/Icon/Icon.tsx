import type {
  Icon as NativeTablerIcon,
  IconProps as TablerIconProps
} from '@tabler/icons-react';
import { type VariantProps, tv } from 'tailwind-variants';

export const iconStyles = tv({
  base: 'shrink-0',
  variants: {
    size: {
      sm: 'size-3',
      md: 'size-4',
      lg: 'size-5',
      xl: 'size-6'
    },
    colorRole: {
      primary: 'stroke-text-primary',
      muted: 'stroke-text-muted',
      brand: 'stroke-text-brand',
      success: 'stroke-text-success',
      warning: 'stroke-text-warning',
      danger: 'stroke-text-danger'
    }
  },
  defaultVariants: {
    size: 'md'
  }
});

type TablerIcon = React.ForwardRefExoticComponent<
  Omit<TablerIconProps, 'ref'> & React.RefAttributes<NativeTablerIcon>
>;

type IconSvgComponent = React.FC<React.SVGProps<SVGSVGElement>>;

export type IconProp = TablerIcon | IconSvgComponent;

export interface IconProps extends VariantProps<typeof iconStyles> {
  icon: IconProp;
  className?: string;
  stroke?: string;
}

const Icon = ({
  icon,
  size,
  colorRole,
  className,
  stroke = '2.5'
}: IconProps) => {
  const Comp = icon;

  return (
    <Comp
      className={iconStyles({ size, colorRole, className })}
      strokeWidth={stroke}
      stroke={stroke}
    />
  );
};

export default Icon;
