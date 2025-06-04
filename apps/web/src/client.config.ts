import getAppUrl from './utils/get-app-url';

const clientConfig = {
  appUrl: getAppUrl()
} as const;

export default clientConfig;
