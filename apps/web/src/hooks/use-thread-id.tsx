import { usePathname } from 'next/navigation';

const useThreadId = () => {
  const pathname = usePathname();
  const threadId = pathname.split('/').pop();
  return threadId;
};

export default useThreadId;
