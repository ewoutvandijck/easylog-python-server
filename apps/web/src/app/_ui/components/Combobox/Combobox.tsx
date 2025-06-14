import * as PopoverPrimitive from '@radix-ui/react-popover';

import Popover from '@/app/_ui/components/Popover/Popover';

import useComboboxContext from './useComboboxContext';

export interface ComboboxProps extends PopoverPrimitive.PopoverProps {}

const Combobox = (props: ComboboxProps) => {
  const { open, setOpen } = useComboboxContext();

  return <Popover {...props} open={open} onOpenChange={setOpen} />;
};

export default Combobox;
