import {
  Configuration,
  ConfigurationParameters,
  HealthApi,
  MessagesApi,
  ThreadsApi
} from './generated-client';

export const createClient = (config: ConfigurationParameters) => {
  const client = {
    health: new HealthApi(new Configuration(config)),
    messages: new MessagesApi(new Configuration(config)),
    threads: new ThreadsApi(new Configuration(config))
  };

  return client;
};

export default createClient;
