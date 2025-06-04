import { betterAuth } from 'better-auth';
import { drizzleAdapter } from 'better-auth/adapters/drizzle';
import { nextCookies } from 'better-auth/next-js';
import { passkey } from 'better-auth/plugins/passkey';
import { eq } from 'drizzle-orm';

import slugify from '@/app/_ui/utils/slugify';
import db from '@/database/client';
import * as schema from '@/database/schema';
import { organizationMembers } from '@/database/schema';
import { organizations } from '@/database/schema';
import serverConfig from '@/server.config';

const authServerClient = betterAuth({
  baseURL: serverConfig.appUrl.toString(),
  secret: serverConfig.betterAuthSecret,
  plugins: [nextCookies(), passkey()],
  advanced: {
    database: {
      generateId: () => crypto.randomUUID()
    }
  },
  database: drizzleAdapter(db, {
    provider: 'pg',
    usePlural: true,
    schema
  }),
  emailAndPassword: {
    enabled: true
  },
  socialProviders: {
    google: {
      clientId: serverConfig.googleOauthClientId,
      clientSecret: serverConfig.googleOauthClientSecret
    }
  },
  databaseHooks: {
    user: {
      create: {
        after: async (user) => {
          const userName = user.name ?? user.email.split('@')[0];

          let slug = slugify(userName);

          const slugExists =
            (
              await db
                .select()
                .from(organizations)
                .where(eq(organizations.slug, slug))
                .limit(1)
            ).length > 0;

          if (slugExists) {
            slug = `${slug}-${user.id.slice(0, 4)}`;
          }

          const [organization] = await db
            .insert(organizations)
            .values({
              name: userName,
              slug
            })
            .returning();

          await db.insert(organizationMembers).values({
            userId: user.id,
            organizationId: organization.id
          });
        }
      }
    }
  }
});

export default authServerClient;
