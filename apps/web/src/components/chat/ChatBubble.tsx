import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { DynamicChart } from '@/components/charts/DynamicChart';
import { MessageResponseContentInner } from '@/lib/api/generated-client';
import { multipleChoiceSchema } from '@/schemas/multipleChoice';
import useSendMessage from '@/hooks/use-send-message';
import useThreadId from '@/hooks/use-thread-id';
import useConfigurations from '@/hooks/use-configurations';

export interface ChatBubbleProps {
  content: MessageResponseContentInner;
  role: 'user' | 'assistant' | 'system' | 'developer' | 'tool';
}

const ChatBubble = ({ content, role }: ChatBubbleProps) => {
  const threadId = useThreadId();
  const { sendMessage } = useSendMessage();
  const { activeConfiguration } = useConfigurations();

  return (
    <div
      className={cn(
        'rounded-lg px-4 py-1 max-w-lg bg-secondary flex flex-col',
        role === 'user' ? 'ml-auto' : 'mr-auto',
        (content.type === 'tool_result' &&
          (content.widget_type === 'image' ||
            content.widget_type === 'image_url')) ||
          content.type === 'image'
          ? 'p-0 border border-secondary'
          : null,
        content.type === 'tool_result' &&
          content.widget_type === 'chart' &&
          'p-0 w-[32rem]'
      )}
    >
      {content.type === 'text' ||
      (content.type === 'tool_result' && content.widget_type === 'text') ? (
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Customize link behavior
            a: ({ ...props }) => (
              <a
                {...props}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline break-words"
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
              <div className="overflow-x-auto">
                <table
                  {...props}
                  className="border-collapse table-auto w-full my-4 overflow-hidden rounded-lg max-w-full overflow-x-auto"
                />
              </div>
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
          {content.type === 'text' ? content.text : content.output}
        </ReactMarkdown>
      ) : content.type === 'tool_result' &&
        (content.widget_type === 'image' ||
          content.widget_type === 'image_url') ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={content.output} alt="tool result" className="rounded-lg" />
      ) : content.type === 'tool_result' && content.widget_type === 'chart' ? (
        <DynamicChart chartJson={content.output} />
      ) : content.type === 'image' ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={content.image_url} alt="tool result" className="rounded-lg" />
      ) : content.type === 'tool_result' &&
        content.widget_type === 'multiple_choice' ? (
        <div className="flex flex-col gap-2">
          {multipleChoiceSchema
            .parse(JSON.parse(content.output))
            .choices.map((choice) => (
              <button
                key={choice.value}
                className="rounded-lg px-4 py-2 bg-secondary"
                onClick={() => {
                  sendMessage(threadId!, {
                    agent_config: {
                      agent_class:
                        activeConfiguration?.agentConfig.agent_class ?? '',
                      ...activeConfiguration?.agentConfig
                    },
                    content: [
                      {
                        text: choice.value,
                        type: 'text'
                      }
                    ]
                  });
                }}
              >
                {choice.label}
              </button>
            ))}
        </div>
      ) : null}
    </div>
  );
};

export default ChatBubble;
