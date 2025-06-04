import { HydrationBoundary, dehydrate } from '@tanstack/react-query';

import DocumentsDropzone from '@/app/_documents/components/DocumentsDropzone';
import DocumentsTable from '@/app/_documents/components/DocumentsTable';
import PageHeader from '@/app/_ui/components/PageHeader/PageHeader';
import PageHeaderContent from '@/app/_ui/components/PageHeader/PageHeaderContent';
import PageHeaderTitle from '@/app/_ui/components/PageHeader/PageHeaderTitle';
import getQueryClient from '@/lib/react-query';
import api from '@/lib/trpc/server';

const KnowledgePage = async ({
  params
}: {
  params: Promise<{ organizationSlug: string }>;
}) => {
  const { organizationSlug } = await params;

  const queryClient = getQueryClient();
  await queryClient.prefetchQuery(
    api.documents.getMany.queryOptions({
      organizationId: organizationSlug
    })
  );

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <PageHeader>
        <PageHeaderContent>
          <PageHeaderTitle>Documents</PageHeaderTitle>
        </PageHeaderContent>
      </PageHeader>
      <main className="grow overflow-y-scroll p-4">
        <DocumentsDropzone>
          <DocumentsTable />
        </DocumentsDropzone>
      </main>
    </HydrationBoundary>
  );
};

export default KnowledgePage;
