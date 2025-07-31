import { IconCheck, IconSearch } from '@tabler/icons-react';

import ContentWrapper from '@/app/_ui/components/ContentWrapper/ContentWrapper';
import IconSpinner from '@/app/_ui/components/Icon/IconSpinner';
import Typography from '@/app/_ui/components/Typography/Typography';

export interface ChatMessageAssistantDocumentSearchProps {
  status:
    | 'searching_documents'
    | 'documents_found'
    | 'researching_document'
    | 'document_research_complete';
  content: string;
}

const getIcon = (status: ChatMessageAssistantDocumentSearchProps['status']) => {
  switch (status) {
    case 'searching_documents':
      return IconSpinner;
    case 'documents_found':
      return IconSearch;
    case 'researching_document':
      return IconSpinner;
    case 'document_research_complete':
      return IconCheck;
  }
};

const getLabel = (
  status: ChatMessageAssistantDocumentSearchProps['status']
) => {
  switch (status) {
    case 'searching_documents':
      return 'Searching documents';
    case 'documents_found':
      return 'Documents found';
    case 'researching_document':
      return 'Researching document';
    case 'document_research_complete':
      return 'Document research complete';
  }
};

const ChatMessageAssistantDocumentSearch = ({
  status,
  content
}: ChatMessageAssistantDocumentSearchProps) => {
  return (
    <div className="bg-surface-muted max-w-lg rounded-xl p-3">
      <Typography variant="bodySm">
        <ContentWrapper iconLeft={getIcon(status)}>
          {getLabel(status)}
        </ContentWrapper>
      </Typography>

      <Typography variant="bodySm" className="text-text-muted">
        {content}
      </Typography>
    </div>
  );
};

export default ChatMessageAssistantDocumentSearch;
