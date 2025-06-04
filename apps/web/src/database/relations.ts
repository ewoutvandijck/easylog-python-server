import { defineRelations } from 'drizzle-orm';

import * as schema from './schema';

const relations = defineRelations(schema, (r) => ({
  users: {
    sessions: r.many.sessions({
      from: r.users.id,
      to: r.sessions.userId
    }),
    accounts: r.many.accounts({
      from: r.users.id,
      to: r.accounts.userId
    }),
    passkeys: r.many.passkeys({
      from: r.users.id,
      to: r.passkeys.userId
    }),
    organizationMembers: r.many.organizationMembers({
      from: r.users.id,
      to: r.organizationMembers.userId
    }),
    organizations: r.many.organizations({
      from: r.users.id.through(r.organizationMembers.userId),
      to: r.organizations.id.through(r.organizationMembers.organizationId)
    })
  },
  sessions: {
    user: r.one.users({
      from: r.sessions.userId,
      to: r.users.id,
      optional: false
    })
  },
  accounts: {
    user: r.one.users({
      from: r.accounts.userId,
      to: r.users.id,
      optional: false
    })
  },
  passkeys: {
    user: r.one.users({
      from: r.passkeys.userId,
      to: r.users.id,
      optional: false
    })
  },
  organizations: {
    organizationMembers: r.many.organizationMembers({
      from: r.organizations.id,
      to: r.organizationMembers.organizationId
    }),
    members: r.many.users({
      from: r.organizations.id.through(r.organizationMembers.organizationId),
      to: r.users.id.through(r.organizationMembers.userId),
      alias: 'organizationMember'
    })
  },
  organizationMembers: {
    organization: r.one.organizations({
      from: r.organizationMembers.organizationId,
      to: r.organizations.id,
      optional: false
    }),
    user: r.one.users({
      from: r.organizationMembers.userId,
      to: r.users.id,
      optional: false
    })
  },
  verifications: {}
}));

export default relations;
