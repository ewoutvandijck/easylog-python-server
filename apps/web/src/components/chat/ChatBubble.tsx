import { MessageContents } from '@/lib/api/generated-client';
import { cn } from '@/lib/utils';

export interface ChatBubbleProps {
  contents: Partial<MessageContents>[];
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
      {contents.map((content, i) => {
        // Check content type
        if (content.type === 'image' && typeof content.content === 'string') {
          return (
            <img
              key={i}
              src={content.content}
              alt="Chat image"
              className="max-w-full h-auto rounded-md animate-in fade-in"
            />
          );
        }

        // Default to text content
        return (
          <span key={i} className="animate-in fade-in">
            {content.content}
          </span>
        );
      })}
    </div>
  );
};

export default ChatBubble;
