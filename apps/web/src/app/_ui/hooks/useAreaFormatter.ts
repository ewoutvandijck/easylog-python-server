import { useLocale, useTranslations } from 'next-intl';

const useAreaFormatter = () => {
  const locale = useLocale();
  const t = useTranslations();

  return (
    value: number | string,
    {
      min,
      max,
      ...options
    }: Intl.NumberFormatOptions & {
      min?: string | number;
      max?: string | number;
    } = {}
  ) => {
    if (value === '') return '';

    let numericValue = Number(value);

    if (min !== undefined && numericValue < Number(min))
      numericValue = Number(min);

    if (max !== undefined && numericValue > Number(max))
      numericValue = Number(max);

    const formattedValue = Intl.NumberFormat(locale, {
      style: 'decimal',
      maximumFractionDigits: 0,
      useGrouping: true,
      ...options
    }).format(numericValue);

    return t('crazy_nimble_boar_race', { value: formattedValue });
  };
};

export default useAreaFormatter;
