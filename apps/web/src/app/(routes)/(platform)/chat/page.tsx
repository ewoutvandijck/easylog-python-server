import ChatHistory from '@/app/_chat/components/ChatHistory';
import ChatInput from '@/app/_chat/components/ChatInput';
import ChatProvider from '@/app/_chat/components/ChatProvider';

const ChatPage = async () => {
  return (
    <ChatProvider>
      <ChatHistory />
      <ChatInput />
    </ChatProvider>
  );
};

export default ChatPage;
