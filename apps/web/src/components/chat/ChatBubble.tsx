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
        role === 'user' ? 'ml-auto' : 'mr-auto'
      )}
    >
      <span className="animate-in fade-in">
        {content.type === 'text'
          ? content.content
          : content.type === 'text_delta'
            ? content.content
            : content.type === 'tool_result' &&
                content.content_format !== 'image'
              ? content.content
              : null}
      </span>
    </div>
  );
};

export default ChatBubble;
