'use client';

import {
  IconChevronDown,
  IconChevronLeft,
  IconChevronRight,
  IconChevronUp
} from '@tabler/icons-react';
import { nl } from 'date-fns/locale';
import { DayPicker } from 'react-day-picker';

import Icon from '../Icon/Icon';

export type CalendarProps = React.ComponentProps<typeof DayPicker>;

function Calendar({
  classNames,
  showOutsideDays = true,
  ...props
}: CalendarProps) {
  return (
    <DayPicker
      locale={nl}
      showOutsideDays={showOutsideDays}
      classNames={{
        button_next:
          'absolute top-0 right-0 size-8 bg-fill-primary rounded-lg hover:bg-fill-primary-hover active:bg-fill-primary-active flex items-center justify-center',
        button_previous:
          'absolute top-0 left-0 size-8 bg-fill-primary rounded-lg hover:bg-fill-primary-hover active:bg-fill-primary-active flex items-center justify-center',
        caption_label: 'font-heading font-medium text-text-primary text-sm',
        chevron: 'style-module__FXs-Ia__chevron',
        day: 'size-8 text-center p-0',
        day_button:
          'size-8 justify-center items-center font-normal text-sm hover:text-text-primary-hover text-text-primary rounded-lg hover:bg-fill-primary-hover active:bg-fill-primary-active',
        disabled: 'style-module__FXs-Ia__disabled',
        dropdown: 'style-module__FXs-Ia__dropdown',
        dropdown_root: 'style-module__FXs-Ia__dropdown_root',
        dropdowns: 'style-module__FXs-Ia__dropdowns',
        hidden: 'style-module__FXs-Ia__hidden',
        month_caption: 'flex justify-center items-center h-8',
        month: 'not-last:mr-3',
        month_grid: 'style-module__FXs-Ia__month_grid border-collapse',
        months: 'flex relative',
        nav: 'style-module__FXs-Ia__nav',
        outside: 'opacity-25',
        range_middle: 'style-module__FXs-Ia__range_middle',
        range_start:
          '[&>button]:rounded-lg [&>button]:bg-fill-brand [&>button]:text-text-primary-on-fill! hover:[&>button]:bg-fill-brand-hover active:[&>button]:bg-fill-brand-active rounded-tl-lg rounded-bl-lg',
        range_end:
          '[&>button]:rounded-lg [&>button]:bg-fill-brand [&>button]:text-text-primary-on-fill! hover:[&>button]:bg-fill-brand-hover active:[&>button]:bg-fill-brand-active rounded-tr-lg rounded-br-lg',
        root: 'style-module__FXs-Ia__root',
        selected: 'bg-fill-primary-selected',
        today: 'style-module__FXs-Ia__today',
        week: 'flex w-full mt-2',
        weekdays: 'flex w-full mt-2',
        week_number: 'style-module__FXs-Ia__week_number',
        weekday: 'text-sm font-heading font-medium text-text-muted size-8',
        ...classNames
      }}
      components={{
        Chevron: ({ size: _, orientation, ...props }) => (
          <Icon
            icon={
              orientation === 'down'
                ? IconChevronDown
                : orientation === 'left'
                  ? IconChevronLeft
                  : orientation === 'up'
                    ? IconChevronUp
                    : IconChevronRight
            }
            {...props}
          />
        )
      }}
      {...props}
    />
  );
}
Calendar.displayName = 'Calendar';

export { Calendar };
