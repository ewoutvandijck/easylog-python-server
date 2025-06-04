import { useRouter } from 'next/navigation';

import useSearchParams from './useSearchParams';

const useSearchAwareRouter = () => {
  const searchParams = useSearchParams();
  const router = useRouter();

  const push = (route: string) => {
    if (searchParams) {
      router.push(`${route}?${searchParams.toString()}`);
    }

    router.push(route);
  };

  return { ...router, push };
};

export default useSearchAwareRouter;
