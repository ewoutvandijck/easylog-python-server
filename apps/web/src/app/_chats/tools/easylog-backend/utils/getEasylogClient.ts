import authServerClient from '@/lib/better-auth/server';
import createClient from '@/lib/easylog/client';

const getEasylogClient = async (userId: string) => {
  const { accessToken } = await authServerClient.api.getAccessToken({
    body: {
      providerId: 'easylog',
      userId
    }
  });

  if (!accessToken) {
    throw new Error('No access token');
  }

  return createClient({
    apiKey: accessToken,
    basePath: 'https://staging2.easylog.nu/api'
  });
};

export default getEasylogClient;
