import { VariantProps, tv } from 'tailwind-variants';

export const bannerContentStyles = tv({
  base: 'flex items-center justify-start gap-2'
});

export interface BannerContentProps
  extends VariantProps<typeof bannerContentStyles> {
  className?: string;
}

const BannerContent = ({
  className,
  children
}: React.PropsWithChildren<BannerContentProps>) => {
  return <div className={bannerContentStyles({ className })}>{children}</div>;
};

export default BannerContent;
