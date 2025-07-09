'use client';

import { useLocale } from 'next-intl';

export interface DateComponentProps extends Intl.DateTimeFormatOptions {
  date: Date;
}

const DateComponent = ({ date, ...options }: DateComponentProps) => {
  const locale = useLocale();
  return Intl.DateTimeFormat(locale, {
    ...options
  }).format(date);
};

export default DateComponent;
