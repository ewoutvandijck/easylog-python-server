'use client';

import Image from 'next/image';
import { useState } from 'react';
import { VariantProps, tv } from 'tailwind-variants';

import getSupabaseImageLoader from '@/lib/supabase/imageLoader';

import EmptyAvatar from './images/empty-avatar.png';
import Typography from '../Typography/Typography';

export const avatarStyles = tv({
  base: 'flex overflow-hidden',
  variants: {
    size: {
      xs: 'size-6',
      sm: 'size-8',
      md: 'size-9',
      lg: 'size-10',
      xl: 'size-11'
    },
    shape: {
      rect: 'rounded-md',
      circle: 'rounded-full'
    },
    isLoaded: {
      false: 'bg-surface-muted'
    },
    hasImage: {
      true: '',
      false: 'items-center justify-center'
    }
  },
  compoundVariants: [
    {
      shape: 'rect',
      size: 'sm',
      className: 'rounded-sm'
    },
    {
      shape: 'rect',
      size: 'xs',
      className: 'rounded-sm'
    }
  ],
  defaultVariants: {
    size: 'md',
    shape: 'rect'
  }
});

export interface AvatarProps extends VariantProps<typeof avatarStyles> {
  className?: string;
  src?: string;
  url?: URL | string;
  bucket?: string;
  fallback?: string;
  fallbackType?: 'letter' | 'image';
  fallbackSeed?: string | number;
}

const Avatar = ({
  src: _src,
  fallback,
  fallbackType = 'image',
  bucket,
  url,
  className,
  ...props
}: AvatarProps) => {
  const [hasError, setHasError] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  const splittedFallback = fallback?.split(' ');

  const firstTwoLetters =
    splittedFallback && splittedFallback.length > 1
      ? splittedFallback
          .map((word) => word[0])
          .slice(0, 2)
          .join('')
          .toUpperCase()
      : fallback
        ? fallback.slice(0, 2).toUpperCase()
        : fallback;

  const src = url ? `/api/favicon/${new URL(url).hostname}` : _src;

  const hasImage = src && !hasError;

  return (
    <div
      className={avatarStyles({
        ...props,
        isLoaded,
        hasImage: !!hasImage,
        className
      })}
    >
      {hasImage ? (
        <Image
          className="object-cover"
          src={src}
          alt={fallback ?? 'Avatar'}
          width={64}
          height={64}
          loader={_src ? getSupabaseImageLoader(bucket) : () => src}
          onLoad={() => {
            setIsLoaded(true);
            setHasError(false);
          }}
          onError={() => {
            setHasError(true);
          }}
        />
      ) : fallbackType === 'image' ? (
        <Image src={EmptyAvatar} alt={fallback ?? 'Avatar'} />
      ) : (
        <Typography variant="bodyXs">{firstTwoLetters}</Typography>
      )}
    </div>
  );
};

export default Avatar;
