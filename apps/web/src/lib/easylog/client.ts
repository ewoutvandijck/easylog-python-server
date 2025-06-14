import {
  AllocationsApi,
  AnnouncementsApi,
  AuthenticationApi,
  ChatsAlphaApi,
  Configuration,
  DatasourcesApi,
  DefaultApi,
  PlanningApi,
  PlanningPhasesApi,
  PlanningResourcesApi
} from './generated-client/index';

export interface ClientConfig {
  apiKey: string;
  basePath?: string;
}

const createClient = ({
  apiKey,
  basePath = 'https://staging2.easylog.nu/api'
}: ClientConfig) => {
  const config = new Configuration({
    basePath,
    accessToken: apiKey
  });

  return {
    chatsAlpha: new ChatsAlphaApi(config),
    announcements: new AnnouncementsApi(config),
    authentication: new AuthenticationApi(config),
    default: new DefaultApi(config),
    datasources: new DatasourcesApi(config),
    planning: new PlanningApi(config),
    planningPhases: new PlanningPhasesApi(config),
    planningResources: new PlanningResourcesApi(config),
    allocations: new AllocationsApi(config)
  };
};

export default createClient;
