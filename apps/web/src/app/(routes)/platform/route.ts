import { redirect } from 'next/navigation';
import { NextRequest } from 'next/server';

import db from '@/database/client';
import authServerClient from '@/lib/better-auth/server';

export const GET = async (request: NextRequest) => {
  const session = await authServerClient.api.getSession({
    headers: request.headers
  });

  if (!session) {
    return new Response('Unauthorized', { status: 401 });
  }

  const user = await db.query.users.findFirst({
    where: {
      id: session.user.id
    },
    with: {
      organizations: true
    }
  });

  if (!user) {
    return new Response('User not found', { status: 404 });
  }

  if (!user.organizations.length) {
    return new Response('User has no organizations', { status: 404 });
  }

  const organization = user.organizations[0];
  redirect(`/platform/${organization.slug}/documents`);
};
