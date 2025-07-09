import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface ChatMessageAssistantMarkdownContentProps {
  text: string;
}

const ChatMessageAssistantMarkdownContent = ({
  text
}: ChatMessageAssistantMarkdownContentProps) => {
  return (
    <div className="prose rounded-xl p-3">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  );
};

export default ChatMessageAssistantMarkdownContent;
