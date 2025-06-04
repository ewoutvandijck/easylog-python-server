import { NumberFormatBase, NumberFormatBaseProps } from 'react-number-format';

import useAreaFormatter from '../../hooks/useAreaFormatter';

export interface AreaInputProps extends NumberFormatBaseProps {}

const AreaInput = ({ min, max, ...props }: AreaInputProps) => {
  const format = useAreaFormatter();

  return (
    <NumberFormatBase
      {...props}
      format={(value) => format(value, { min, max })}
    />
  );
};

export default AreaInput;
