import { ColumnDef } from '@tanstack/react-table';

import DataTableColumnHeader from '@/app/_ui/components/DataTable/DataTableColumnHeader';
import Typography from '@/app/_ui/components/Typography/Typography';
import { RouterOutputs } from '@/trpc-router';

export type DocumentRowProps = RouterOutputs['documents']['getMany'][number];

export const documentsTableColumns: ColumnDef<DocumentRowProps>[] = [
  {
    accessorKey: 'path',
    enableSorting: true,
    size: 300,
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Path" />
    ),
    cell: ({ row }) => (
      <Typography variant="bodySm">{row.original.path}</Typography>
    )
  },
  {
    accessorKey: 'type',
    enableSorting: true,
    size: 150,
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Type" />
    ),
    cell: ({ row }) => (
      <Typography variant="bodySm">{row.original.type}</Typography>
    )
  },
  {
    accessorKey: 'summary',
    enableSorting: true,
    size: 150,
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Summary" />
    ),
    cell: ({ row }) => (
      <Typography variant="bodySm">{row.original.summary}</Typography>
    )
  },
  {
    accessorKey: 'tags',
    enableSorting: true,
    size: 100,
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Tags" />
    ),
    cell: ({ row }) => (
      <Typography variant="bodySm">{row.original.tags?.join(', ')}</Typography>
    )
  }
];
