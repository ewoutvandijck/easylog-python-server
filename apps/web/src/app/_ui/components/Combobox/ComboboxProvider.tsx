'use client';

import Fuse, { IFuseOptions } from 'fuse.js';
import { createContext, useState } from 'react';

export type ItemWithId = {
  id: number | string;
} & Record<string, unknown>;

export interface ComboboxContextType<T = ItemWithId> {
  items: ReadonlyArray<T>;

  activeItem: T | null;

  open: boolean;
  setOpen: (open: boolean) => void;

  value: string | number | null;
  setValue: (value: string | number | null) => void;

  search: string;
  setSearch: (search: string) => void;

  results: ReadonlyArray<T>;
}

export const ComboboxContext = createContext<ComboboxContextType | null>(null);

export interface ComboboxProviderProps<T = ItemWithId> {
  items: ReadonlyArray<T>;
  value?: number | string | null;
  defaultValue?: number | string | null;
  onValueChange?: (value: number | string | null) => void;
  fuseOptions?: IFuseOptions<T>;
}

const ComboboxProvider = ({
  items,
  value: _value,
  onValueChange,
  defaultValue = null,
  fuseOptions,
  children
}: React.PropsWithChildren<ComboboxProviderProps>) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');

  const [__value, __setValue] = useState<string | number | null>(defaultValue);

  const value = _value ?? __value;

  const setValue = (value: string | number | null) => {
    __setValue(value);
    onValueChange?.(value);
  };

  const fuse = new Fuse(items, fuseOptions);

  const results = search
    ? fuse.search(search).map((result) => result.item)
    : items;

  const activeItem = value
    ? (items.find((item) => item.id?.toString() === value.toString()) ?? null)
    : null;

  return (
    <ComboboxContext.Provider
      value={{
        items,
        activeItem,
        open,
        setOpen,
        value,
        setValue,
        search,
        setSearch,
        results
      }}
    >
      {children}
    </ComboboxContext.Provider>
  );
};

export default ComboboxProvider;
