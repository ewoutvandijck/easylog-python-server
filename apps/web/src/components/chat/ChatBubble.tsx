import { MessageContent } from '@/app/schemas/message-contents';
import { cn } from '@/lib/utils';

export interface ChatBubbleProps {
  content: MessageContent;
  role: 'user' | 'assistant' | 'system' | 'developer';
}

const ChatBubble = ({ content, role }: ChatBubbleProps) => {
  return (
    <div
      className={cn(
        'rounded-lg px-4 py-2 max-w-lg bg-secondary',
        role === 'user' ? 'ml-auto' : 'mr-auto',
        content.type === 'tool_result' &&
          content.content_format === 'image' &&
          'p-0 border border-secondary'
      )}
    >
      <span className="animate-in fade-in">
        {content.type === 'text' ? (
          content.content
        ) : content.type === 'text_delta' ? (
          content.content
        ) : content.type === 'tool_result' &&
          content.content_format !== 'image' ? (
          content.content
        ) : content.type === 'tool_result' &&
          content.content_format === 'image' ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={content.content} alt="tool result" className="rounded-lg" />
        ) : null}
      </span>
    </div>
  );
};

export default ChatBubble;
