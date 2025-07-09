import { useLocale } from 'next-intl';

const useCurrencyFormatter = () => {
  const locale = useLocale();

  return (value: number | string, options: Intl.NumberFormatOptions = {}) => {
    if (value === '') return '';
    if (typeof value === 'string') {
      value = Number(value);
    }

    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
      ...options
    }).format(value);
  };
};

export default useCurrencyFormatter;
