import clientEnv from '@/client.env';

/**
 * Get the fully qualified app url (including protocol and port)
 *
 * @returns The app url
 */
const getAppUrl = () => {
  let url =
    clientEnv.NEXT_PUBLIC_APP_URL ??
    clientEnv.NEXT_PUBLIC_VERCEL_URL ??
    'http://localhost:3000';

  if (!url.startsWith('http')) {
    url = `https://${url}`;
  }

  return new URL(url);
};

export default getAppUrl;
