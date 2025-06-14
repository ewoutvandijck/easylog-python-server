'use client';

import type { LinkProps } from 'next/link';
import { type Locale } from 'next-intl';
import { useMemo } from 'react';

import { Link } from '@/i18n/routing';

import useSearchParams from '../../hooks/useSearchParams';

type NextLinkFullPRops = Omit<
  React.AnchorHTMLAttributes<HTMLAnchorElement>,
  keyof LinkProps
> &
  LinkProps & {
    locale?: Locale;
  };

export interface SearchAwareLinkProps extends NextLinkFullPRops {
  preserveSearch?: boolean;
  href: string | URL;
  isExternal?: boolean;
}

/** A wrapper around Next.js Link that preserves search params when navigating. */
const SearchAwareLink = ({
  preserveSearch,
  href,
  isExternal = false,
  rel,
  target,
  ...props
}: SearchAwareLinkProps) => {
  const searchParams = useSearchParams();

  const hrefWithSearch = useMemo(() => {
    if (searchParams && preserveSearch) {
      return `${href}?${searchParams.toString()}`;
    }

    return href;
  }, [href, searchParams, preserveSearch]);

  return (
    <Link
      {...props}
      href={hrefWithSearch}
      rel={isExternal ? 'noopener noreferrer' : rel}
      target={isExternal ? '_blank' : target}
    />
  );
};

export default SearchAwareLink;
