'use client';

import { useEffect, useState } from 'react';

import Input, { InputProps } from '../Input/Input';

export interface DateProps extends Omit<InputProps, 'value'> {
  value?: Date | string | null;
  onValueChange?: (value: Date | null) => void;
}

const DateInput = ({
  value: _value,
  onChange,
  onValueChange,
  ...props
}: DateProps) => {
  const safeParseDateString = (value: string) => {
    try {
      const date = new Date(value);
      return isNaN(date.getTime()) ? null : date;
    } catch {
      return null;
    }
  };

  const getRawValue = (value?: Date | string | null) => {
    if (value instanceof Date) {
      return value.toISOString().split('T')[0];
    } else if (typeof value === 'string') {
      return safeParseDateString(value)?.toISOString().split('T')[0] ?? '';
    }

    return '';
  };

  const [rawValue, setRawValue] = useState<string>(getRawValue(_value));

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange?.(e);

    setRawValue(e.target.value);

    const date = safeParseDateString(e.target.value);
    onValueChange?.(date);
  };

  useEffect(() => {
    if (_value instanceof Date) {
      setRawValue(_value.toISOString().split('T')[0]);
    } else if (typeof _value === 'string') {
      setRawValue(
        safeParseDateString(_value)?.toISOString().split('T')[0] ?? ''
      );
    } else {
      setRawValue('');
    }
  }, [_value]);

  return (
    <Input type="date" value={rawValue} {...props} onChange={handleChange} />
  );
};

export default DateInput;
