export interface ChatMessageUserTextContentProps {
  text: string;
}

const ChatMessageUserTextContent = ({
  text
}: ChatMessageUserTextContentProps) => {
  return (
    <div className="bg-surface-muted prose max-w-lg rounded-xl p-3">
      {text.split('\n').map((line, index) => (
        <p key={index}>{line}</p>
      ))}
    </div>
  );
};

export default ChatMessageUserTextContent;
