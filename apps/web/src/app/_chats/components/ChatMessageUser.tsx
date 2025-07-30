import { motion } from 'motion/react';

const ChatMessageUser = ({ children }: React.PropsWithChildren) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, filter: 'blur(5px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.2 }}
      className="my-3 flex w-full justify-end"
    >
      {children}
    </motion.div>
  );
};

export default ChatMessageUser;
