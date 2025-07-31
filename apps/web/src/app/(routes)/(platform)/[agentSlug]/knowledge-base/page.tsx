import { HydrationBoundary, dehydrate } from '@tanstack/react-query';

import DocumentsActionRow from '@/app/_documents/components/DocumentsActionRow';
import DocumentsDataTable from '@/app/_documents/components/DocumentsDataTable';
import getQueryClient from '@/lib/react-query';
import api from '@/lib/trpc/server';

const KnowledgeBasePage = async ({
  params
}: {
  params: Promise<{ agentSlug: string }>;
}) => {
  const { agentSlug } = await params;

  const queryClient = getQueryClient();

  void queryClient.prefetchInfiniteQuery(
    api.documents.getMany.infiniteQueryOptions({
      cursor: 0,
      limit: 100,
      agentId: agentSlug
    })
  );

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <div className="container my-12 flex flex-col gap-4">
        <DocumentsActionRow agentSlug={agentSlug} />
        <DocumentsDataTable agentSlug={agentSlug} />
      </div>
    </HydrationBoundary>
  );
};

export default KnowledgeBasePage;
