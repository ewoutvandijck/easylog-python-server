'use client';

import { useSuspenseQuery } from '@tanstack/react-query';

import useOrganizationSlug from '@/app/_organizations/hooks/useOrganizationSlug';
import DataTable from '@/app/_ui/components/DataTable/DataTable';
import useTRPC from '@/lib/trpc/browser';

import { documentsTableColumns } from '../table-columns/DocumentsTableColumns';

const DocumentsTable = () => {
  const api = useTRPC();
  const organizationSlug = useOrganizationSlug();

  const { data: documents } = useSuspenseQuery(
    api.documents.getMany.queryOptions({
      organizationId: organizationSlug
    })
  );

  return <DataTable columns={documentsTableColumns} data={documents} />;
};

export default DocumentsTable;
