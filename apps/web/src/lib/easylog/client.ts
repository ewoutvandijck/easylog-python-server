import { AllocationsApi, Configuration } from './generated-client/index';

const createClient = ({ apiKey }: { apiKey: string }) => {
  return new AllocationsApi(
    new Configuration({
      basePath: 'https://staging2.easylog.nu/api',
      accessToken: () => apiKey
    })
  );
};

export default createClient;
