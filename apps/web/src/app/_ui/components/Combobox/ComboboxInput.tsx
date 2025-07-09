import useComboboxContext from './useComboboxContext';
import CommandInput, { CommandInputProps } from '../Command/CommandInput';

export interface ComboboxInputProps extends CommandInputProps {}

const ComboboxInput = ({
  value: _value,
  onValueChange,
  ...props
}: ComboboxInputProps) => {
  const { search, setSearch } = useComboboxContext();

  const handleValueChange = (value: string) => {
    onValueChange?.(value);
    setSearch(value);
  };

  const value = _value ?? search;

  return (
    <CommandInput {...props} value={value} onValueChange={handleValueChange} />
  );
};

export default ComboboxInput;
