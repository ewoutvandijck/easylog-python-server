import { MessageContent } from '@/app/schemas/message-contents';
import { cn } from '@/lib/utils';

export interface ChatBubbleProps {
  contents: MessageContent[];
  role: 'user' | 'assistant' | 'system' | 'developer';
}

const ChatBubble = ({ contents, role }: ChatBubbleProps) => {
  return (
    <div
      className={cn(
        'rounded-lg px-4 py-2 max-w-lg bg-secondary',
        role === 'user' ? 'ml-auto' : 'mr-auto'
      )}
    >
      {contents.map((content, i) => (
        <span key={i} className="animate-in fade-in">
          {content.type === 'text' && content.content}
          {content.type === 'text_delta' && content.content}
        </span>
      ))}
    </div>
  );
};

export default ChatBubble;
