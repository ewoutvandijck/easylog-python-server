import * as PopoverPrimitive from '@radix-ui/react-popover';

import useComboboxContext from './useComboboxContext';

export interface ComboboxTriggerProps
  extends PopoverPrimitive.PopoverTriggerProps {}

const ComboboxTrigger = (props: ComboboxTriggerProps) => {
  const { open } = useComboboxContext();

  return (
    <PopoverPrimitive.PopoverTrigger
      {...props}
      role="combobox"
      aria-expanded={open}
    />
  );
};

export default ComboboxTrigger;
