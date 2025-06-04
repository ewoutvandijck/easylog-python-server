import {
  IconArrowDown,
  IconArrowUp,
  IconSelector,
  IconSortAscending,
  IconSortDescending
} from '@tabler/icons-react';
import { Column } from '@tanstack/react-table';
import { VariantProps, tv } from 'tailwind-variants';

import Button from '../Button/Button';
import ButtonContent from '../Button/ButtonContent';
import DropdownMenu from '../DropdownMenu/DropdownMenu';
import DropdownMenuContent from '../DropdownMenu/DropdownMenuContent';
import DropdownMenuContentWrapper from '../DropdownMenu/DropdownMenuContentWrapper';
import DropdownMenuItem from '../DropdownMenu/DropdownMenuItem';
import DropdownMenuTrigger from '../DropdownMenu/DropdownMenuTrigger';
import Icon from '../Icon/Icon';
import Typography from '../Typography/Typography';

export const dataTableColumnHeaderStyles = tv({
  slots: {
    wrapper: 'flex items-center',
    button: '',
    text: ''
  },
  variants: {
    align: {
      start: {
        wrapper: 'justify-start',
        text: 'text-left',
        button: '-ml-2.5'
      },
      center: {
        wrapper: 'justify-center',
        text: 'text-center',
        button: ''
      },
      end: {
        wrapper: 'justify-end',
        text: 'text-right',
        button: '-mr-2.5'
      }
    }
  },
  defaultVariants: {
    align: 'start'
  }
});

export interface DataTableColumnHeaderProps<TData, TValue>
  extends VariantProps<typeof dataTableColumnHeaderStyles>,
    React.HTMLAttributes<HTMLDivElement> {
  column: Column<TData, TValue>;
  title: string;
  className?: string;
}

const { wrapper, text, button } = dataTableColumnHeaderStyles();

const DataTableColumnHeader = <TData, TValue>({
  column,
  title,
  className,
  align,
  ...props
}: DataTableColumnHeaderProps<TData, TValue>) => {
  if (!column.getCanSort()) {
    return (
      <Typography
        variant="labelSm"
        colorRole="primary"
        className={text({ align, className })}
        {...props}
        asChild
      >
        <span>{title}</span>
      </Typography>
    );
  }

  return (
    <div className={wrapper({ align, className })} {...props}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="sm" variant="ghost" className={button({ align })}>
            <ButtonContent
              contentRight={
                <Icon
                  icon={
                    column.getIsSorted() === 'desc'
                      ? IconArrowDown
                      : column.getIsSorted() === 'asc'
                        ? IconArrowUp
                        : IconSelector
                  }
                  colorRole="muted"
                />
              }
            >
              {title}
            </ButtonContent>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem
            onClick={() => {
              column.toggleSorting(false);
            }}
          >
            <DropdownMenuContentWrapper
              contentLeft={<Icon icon={IconSortAscending} colorRole="muted" />}
              align="start"
            >
              Sorteer oplopend
            </DropdownMenuContentWrapper>
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => {
              column.toggleSorting(true);
            }}
          >
            <DropdownMenuContentWrapper
              contentLeft={<Icon icon={IconSortDescending} colorRole="muted" />}
              align="start"
            >
              Sorteer aflopend
            </DropdownMenuContentWrapper>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default DataTableColumnHeader;
