'use client';

import { useLocale } from 'next-intl';

export interface PriceProps extends Intl.NumberFormatOptions {
  price: number;
  currency?: string;
}

const Price = ({ price, currency = 'EUR', ...options }: PriceProps) => {
  const locale = useLocale();
  return Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    ...options
  }).format(price);
};

export default Price;
