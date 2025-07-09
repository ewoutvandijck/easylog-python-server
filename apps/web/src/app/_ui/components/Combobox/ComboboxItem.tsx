import useComboboxContext from './useComboboxContext';
import CommandItem, { CommandItemProps } from '../Command/CommandItem';

export interface ComboboxItemProps extends CommandItemProps {}

const ComboboxItem = ({ value, onSelect, ...props }: ComboboxItemProps) => {
  const { value: currentValue, setValue, setOpen } = useComboboxContext();

  const handleSelectChange = (value: string) => {
    onSelect?.(value);
    setValue(currentValue === value ? null : value);
    setOpen(false);
  };

  return <CommandItem {...props} value={value} onSelect={handleSelectChange} />;
};

export default ComboboxItem;
