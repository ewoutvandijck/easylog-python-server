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
    chats: r.many.chats({
      from: r.users.id,
      to: r.chats.userId
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
  agents: {
    documents: r.many.documents({
      from: r.agents.id,
      to: r.documents.agentId
    }),
    chats: r.many.chats({
      from: r.agents.id,
      to: r.chats.userId
    })
  },
  documents: {
    agent: r.one.agents({
      from: r.documents.agentId,
      to: r.agents.id,
      optional: false
    })
  },
  chats: {
    agent: r.one.agents({
      from: r.chats.agentId,
      to: r.agents.id,
      optional: false
    }),
    user: r.one.users({
      from: r.chats.userId,
      to: r.users.id,
      optional: false
    })
  },
  organizations: {},
  verifications: {}
}));

export default relations;
