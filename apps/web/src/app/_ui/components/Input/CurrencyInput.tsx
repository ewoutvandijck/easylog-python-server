import { NumberFormatBase, NumberFormatBaseProps } from 'react-number-format';

import useCurrencyFormatter from '../../hooks/useCurrencyFormatter';

export interface CurrencyInputProps extends NumberFormatBaseProps {
  options?: Intl.NumberFormatOptions;
}

const CurrencyInput = ({ options, ...props }: CurrencyInputProps) => {
  const formatCurrency = useCurrencyFormatter();

  return (
    <NumberFormatBase
      {...props}
      format={(value) => formatCurrency(value, options)}
    />
  );
};

export default CurrencyInput;
