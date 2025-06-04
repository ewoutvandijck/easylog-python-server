import { Mistral } from '@mistralai/mistralai';

// import serverEnv from '@/server.env';

const mistralClient = new Mistral({
  apiKey: 'serverEnv.MISTRAL_API_KEY'
});

export default mistralClient;
