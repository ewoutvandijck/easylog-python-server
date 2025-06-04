import { cache } from 'react';

import db from '@/database/client';
import authServerClient from '@/lib/better-auth/server';

const getCurrentUser = cache(async (headers: Headers) => {
  const session = await authServerClient.api.getSession({
    headers
  });

  if (!session) {
    return null;
  }

  const user = await db.query.users.findFirst({
    where: {
      id: session.user.id
    }
  });

  if (!user) {
    return null;
  }

  return user;
});

export default getCurrentUser;
