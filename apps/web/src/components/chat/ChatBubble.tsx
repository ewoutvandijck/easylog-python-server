import { MessageContent } from '@/app/schemas/message-contents';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { DynamicChart } from '@/components/charts/DynamicChart';

export interface ChatBubbleProps {
  content: MessageContent;
  role: 'user' | 'assistant' | 'system' | 'developer';
}

const ChatBubble = ({ content, role }: ChatBubbleProps) => {
  return (
    <div
      className={cn(
        'rounded-lg px-4 py-1 max-w-lg bg-secondary flex flex-col',
        role === 'user' ? 'ml-auto' : 'mr-auto',
        content.type === 'tool_result' &&
          content.content_format === 'image' &&
          'p-0 border border-secondary',
        content.type === 'tool_result' &&
          content.content_format === 'chart' &&
          'p-0 w-[32rem]'
      )}
    >
      {content.type === 'text' || content.type === 'text_delta' ? (
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Customize link behavior
            a: ({ ...props }) => (
              <a
                {...props}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline"
              />
            ),
            // Prevent large headings
            h1: ({ ...props }) => (
              <h3 {...props} className="text-lg font-bold mt-4 mb-2" />
            ),
            h2: ({ ...props }) => (
              <h4 {...props} className="text-md font-bold mt-3 mb-2" />
            ),
            // Code blocks and inline code
            code: ({ ...props }) => (
              <code
                {...props}
                className={cn('bg-gray-800 rounded px-1', 'block p-2 my-2')}
              />
            ),
            // Lists
            ul: ({ ...props }) => (
              <ul {...props} className="list-disc pl-4 my-2" />
            ),
            ol: ({ ...props }) => (
              <ol {...props} className="list-decimal pl-4 my-2" />
            ),
            li: ({ ...props }) => <li {...props} className="my-1" />,
            // Blockquotes
            blockquote: ({ ...props }) => (
              <blockquote
                {...props}
                className="border-l-4 border-gray-600 pl-4 my-2 italic"
              />
            ),
            // Paragraphs
            p: ({ ...props }) => <p {...props} className="my-2" />,
            // Tables
            table: ({ ...props }) => (
              <table
                {...props}
                className="border-collapse table-auto w-full my-4 overflow-hidden rounded-lg"
              />
            ),
            thead: ({ ...props }) => (
              <thead {...props} className="bg-gray-800 text-white" />
            ),
            tbody: ({ ...props }) => (
              <tbody {...props} className="bg-gray-50 dark:bg-gray-900" />
            ),
            tr: ({ ...props }) => (
              <tr
                {...props}
                className="border-b border-gray-700 even:bg-gray-100 dark:even:bg-gray-800"
              />
            ),
            th: ({ ...props }) => (
              <th
                {...props}
                className="px-4 py-3 text-left font-bold border-b-2 border-gray-600"
              />
            ),
            td: ({ ...props }) => (
              <td {...props} className="px-4 py-3 border-gray-700" />
            ),
            // Horizontal rule
            hr: ({ ...props }) => (
              <hr {...props} className="my-4 border-gray-600" />
            ),
            // Strong and emphasis
            strong: ({ ...props }) => (
              <strong {...props} className="font-bold" />
            ),
            em: ({ ...props }) => <em {...props} className="italic" />
          }}
        >
          {content.content}
        </ReactMarkdown>
      ) : content.type === 'tool_result' &&
        content.content_format === 'image' ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={content.content} alt="tool result" className="rounded-lg" />
      ) : content.type === 'tool_result' &&
        content.content_format === 'chart' ? (
        <DynamicChart chartJson={content.content} />
      ) : null}
    </div>
  );
};

export default ChatBubble;
