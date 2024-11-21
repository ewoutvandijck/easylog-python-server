import { MessageContent } from '@/lib/api/generated-client';
import { cn } from '@/lib/utils';

export interface ChatBubbleProps {
  contents: MessageContent[];
  role: 'user' | 'assistant';
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
          {content.content}
        </span>
      ))}
    </div>
  );
};

export default ChatBubble;
