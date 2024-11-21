import { CreateThreadThreadsPostRequest } from '@/lib/api/generated-client';
import useApiClient from './use-api-client';
import { useMutation } from '@tanstack/react-query';

const useCreateThread = () => {
  const apiClient = useApiClient();

  return useMutation({
    mutationFn: (params: CreateThreadThreadsPostRequest) =>
      apiClient.threads.createThreadThreadsPost(params)
  });
};

export default useCreateThread;
