# EasyLog Webchat - Developer Documentation

## 📖 Overzicht

De EasyLog Webchat is een **Next.js 15.3.3** applicatie met **React 19** die een AI-powered chat interface biedt. Deze documentatie beschrijft de architectuur, code structuur en development patterns voor ontwikkelaars die aan het systeem werken.

### 📚 Documentatie Focus

- **Code Architectuur**: Hoe de applicatie is opgebouwd
- **Component Patterns**: Herbruikbare development patterns
- **API Integratie**: Services en endpoints
- **Debugging**: Tools en technieken voor development
- **Best Practices**: Security, performance en code kwaliteit

### 🎯 Voor Wie?

Deze documentatie is bedoeld voor:

- Frontend developers die aan de webchat werken
- Backend developers die API's integreren
- DevOps engineers die deployment beheren
- Tech leads die architectuur beslissingen nemen

## 🏗️ Technische Architectuur

### Core Technologies

- **Next.js 15.3.3** met App Router architectuur
- **React 19.1.0** met hooks en context patterns
- **TypeScript 5.7.2** voor complete type safety
- **Tailwind CSS 4.1.7** voor moderne responsive styling
- **Motion 12.17.0** voor smooth animaties
- **tRPC 11.1.0** voor type-safe API communicatie
- **Vercel AI SDK 5.0.0-beta.32** voor streaming chat functionaliteit
- **Drizzle ORM 1.0.0-beta** voor database operaties
- **Zod 3.25.64** voor runtime validation
- **Tanstack Query v5** (React Query) voor server state management
- **Jotai 2.12.4** voor client state management

### UI Component Libraries

- **Radix UI** componenten (alerts, dialogs, dropdowns, tooltips, etc.)
- **Recharts 2.15.3** voor data visualisaties
- **React Hook Form 7.56.2** voor formulier handling
- **Sonner 2.0.3** voor toast notifications
- **cmdk 1.1.1** voor command palette

### Backend Integration

- **OpenRouter** voor AI model access (300+ modellen) via `@openrouter/ai-sdk-provider`
- **Agent-specifieke configuratie** via database (PostgreSQL)
- **Real-time streaming** responses met AI SDK
- **Tool orchestration** met async execution
- **Mistral AI 1.6.0** client voor specifieke AI taken

### Authentication & Security

- **Better Auth 1.2.9** voor authenticatie (niet NextAuth)
- **EasyLog OAuth** integratie met staging2.easylog.nu
- **Session-based** authentication met secure cookies
- **PKCE flow** voor OAuth 2.0

### Storage & Data

- **AWS S3** integratie voor file uploads
- **Weaviate 3.5.5** vector database voor knowledge base
- **PostgreSQL** via Drizzle ORM
- **Vercel Blob** storage support
- **MySQL2** support voor legacy systemen

## 🏛️ Code Architectuur

### Directory Structure

De applicatie gebruikt Next.js App Router met een modulaire structuur:

```
apps/web/src/
├── app/                    # App Router directory
│   ├── _[feature]/        # Feature modules (prefix _ = shared)
│   ├── (routes)/          # Route definitions
│   └── api/               # API endpoints
├── database/              # Database schema & client
├── lib/                   # External service clients
├── utils/                 # Utility functions
└── jobs/                  # Background jobs (Trigger.dev)
```

### Data Flow Architecture

```
User Input → ChatProvider → API Route → AI Service → Tools → Response Stream → UI Update
                                ↓
                          Database (PostgreSQL)
```

### Key Design Patterns

- **Server Components** by default (Next.js 15)
- **Streaming Responses** voor real-time AI chat
- **Type-safe API's** met tRPC en Zod
- **Context Pattern** voor state management
- **Tool Pattern** voor AI functionaliteit

### Environment Variables

```env
# Database
DB_URL="postgresql://..."

# AI Providers
OPENROUTER_API_KEY="sk-or-..."
MISTRAL_API_KEY="..."

# Authentication (Better Auth)
BETTER_AUTH_SECRET="..."

# S3 Storage
S3_ENDPOINT="http://localhost:9000"
S3_REGION="us-east-1"
S3_ACCESS_KEY="miniouser"
S3_SECRET_KEY="miniopassword123"
S3_PUBLIC_BUCKET_NAME="public-storage"

# EasyLog Backend Database
EASYLOG_DB_HOST="..."
EASYLOG_DB_PORT="3306"
EASYLOG_DB_USER="..."
EASYLOG_DB_NAME="..."
EASYLOG_DB_PASSWORD="..."

# Trigger.dev
TRIGGER_SECRET_KEY="..."

# Vercel Blob Storage
BLOB_READ_WRITE_TOKEN="..."
```

## 🧩 Core Components

### ChatProvider (`_chats/components/ChatProvider.tsx`)

```typescript
// Beheert de chat state en AI SDK integratie
const chat = new Chat({
  id: dbChat.id,
  transport: new DefaultChatTransport({
    api: `/api/${agentSlug}/chat`,
  }),
  messages: dbChat.messages,
  dataPartSchemas: { chart, 'document-search' }
})
```

**Verantwoordelijkheid**: Central state management voor chat sessie

### Chat API Route (`api/[agentSlug]/chat/route.ts`)

```typescript
// Streaming endpoint met 800s timeout
streamText({
  model: openrouter(agent.config.model),
  system: promptWithContext,
  messages: convertToModelMessages(messages),
  tools: {
    /* AI tools */
  }
});
```

**Verantwoordelijkheid**: AI model integratie en tool orchestratie

### Tool Implementation Pattern

```typescript
export const toolName = (userId: string) =>
  tool({
    description: 'Tool description',
    inputSchema: z.object({
      /* Zod schema */
    }),
    execute: async (input) => {
      /* Implementation */
    }
  });
```

**Verantwoordelijkheid**: Type-safe tool definities voor AI

### Chat Interface Features

#### Basis Functionaliteit

- **Enter** - Bericht versturen
- **Shift + Enter** - Nieuwe regel
- **Auto-resize** textarea (max 6 regels)
- **Auto-scroll** naar nieuwe berichten
- **Real-time streaming** responses

#### Ondersteunde Content Types

**Text Messages**

```
Gewone tekst berichten met Markdown support
```

**Charts en Visualisaties**

- Bar charts
- Line charts
- Pie charts
- Stacked bar charts

**Document Search**
Real-time zoeken in knowledge base met progress indicators:

1. 🔍 Searching documents...
2. 📄 Documents found
3. 🔬 Researching document
4. ✅ Research complete

#### Tool Capabilities per Agent Type

**EasyLog Agent**

- Planning project management
- Resource allocatie
- SQL queries uitvoeren
- Data source toegang
- Chart generatie

**Healthcare Agents (MUMC)**

- HIPAA-compliant data handling
- ZLM charts voor COPD monitoring
- Medical document search

**Debug Agent**

- Enhanced logging
- Development tools
- 2-hour super agent interval

### Keyboard Shortcuts

- `Enter` - Send message
- `Shift + Enter` - New line
- `Escape` - Clear current input
- `Ctrl/Cmd + K` - Focus input (when available)

## 🔧 Development Guidelines

### File Organization Pattern

```typescript
// Feature modules use underscore prefix for shared components
_chats/              // Shared chat functionality
_auth/               // Shared auth logic
_ui/                 // Reusable UI components

// Routes use parentheses for grouping
(routes)/            // Route group (no URL impact)
(platform)/          // Platform routes group

// Dynamic routes use square brackets
[agentSlug]/         // Dynamic agent parameter
```

### Component Architecture

#### Server vs Client Components

```typescript
// Server Component (default)
// ✅ Data fetching, async operations, secrets
const ServerComponent = async () => {
  const data = await fetchData()
  return <div>{data}</div>
}

// Client Component
// ✅ Interactivity, hooks, browser APIs
'use client'
const ClientComponent = () => {
  const [state, setState] = useState()
  return <button onClick={() => setState()}>Click</button>
}
```

#### Data Fetching Pattern

```typescript
// Server-side data prefetching met React Query
const queryClient = getQueryClient();
await queryClient.prefetchQuery(
  api.chats.getOrCreate.queryOptions({ agentId })
);

// Client-side with Suspense
const { data } = useSuspenseQuery(
  api.chats.getOrCreate.queryOptions({ agentId })
);
```

### Component Structure

```
apps/web/src/app/_chats/
├── components/
│   ├── ChatProvider.tsx       # Main chat context
│   ├── ChatHistory.tsx        # Message rendering
│   ├── ChatInput.tsx          # User input handling
│   ├── ChatMessage*.tsx       # Message type components
└── hooks/
    └── useChatContext.ts      # Chat context hook

apps/web/src/app/_charts/
├── components/
│   ├── BarChart.tsx
│   ├── LineChart.tsx
│   ├── PieChart.tsx
│   └── StackedBarChart.tsx
└── schemas/
    └── internalChartConfigSchema.ts
```

### Adding New Message Types

1. **Define Schema**

```typescript
// schemas/newMessageTypeSchema.ts
const newMessageTypeSchema = z.object({
  status: z.enum(['processing', 'complete']),
  data: z.any()
});
```

2. **Update ChatProvider**

```typescript
// ChatProvider.tsx
dataPartSchemas: {
  'new-message-type': newMessageTypeSchema
}
```

3. **Create Component**

```typescript
// components/ChatMessageAssistantNewType.tsx
const ChatMessageAssistantNewType = ({ data }) => {
  return <div>{/* Render logic */}</div>;
};
```

4. **Add to ChatHistory**

```typescript
// ChatHistory.tsx
part.type === 'data-new-message-type' ? (
  <ChatMessageAssistantNewType data={part.data} />
) : null
```

### Adding New Tools

1. **Create Tool File**

```typescript
// tools/toolNewFeature.ts
export const toolNewFeature = () =>
  tool({
    description: 'Description of new feature',
    inputSchema: z.object({
      param: z.string()
    }),
    execute: async ({ param }) => {
      // Tool logic
      return result;
    }
  });
```

2. **Register in API Route**

```typescript
// api/[agentSlug]/chat/route.ts
tools: {
  newFeature: toolNewFeature(),
  // ... other tools
}
```

### Styling Guidelines

**Tailwind Classes**

- Use design system variables: `bg-surface-primary`, `text-text-primary`
- Mobile-first responsive: `md:px-10`
- Consistent spacing: `p-3 md:p-10`

**Animation Patterns**

```typescript
// Entrance animations
initial={{ opacity: 0, y: '50%', filter: 'blur(5px)' }}
animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}

// State transitions
<AnimatePresence>
  {condition && <motion.div />}
</AnimatePresence>
```

## 🔌 API's & Services

### Core Services Architecture

#### OpenRouter AI Service

```typescript
// lib/ai-providers/openrouter.ts
import { createOpenRouter } from '@openrouter/ai-sdk-provider';
const openrouter = createOpenRouter({
  apiKey: serverConfig.openrouterApiKey
});
// Models: openai/gpt-4.1, anthropic/claude-sonnet-4, etc.
```

#### Database Service (Drizzle ORM)

```typescript
// database/client.ts
import { drizzle } from 'drizzle-orm/postgres-js';
const db = drizzle(postgres(serverConfig.dbUrl), { schema });

// Type-safe queries met relations
const chat = await db.query.chats.findFirst({
  where: { id, userId: user.id },
  with: { agent: true }
});
```

#### tRPC Router Configuration

```typescript
// Server-side query options
const api = createTRPCOptionsProxy({
  ctx: () => createTRPCContext(),
  router: appRouter,
  queryClient: getQueryClient
});

// Client-side hooks
const { data } = useSuspenseQuery(
  api.chats.getOrCreate.queryOptions({ agentId })
);
```

### Main API Endpoints

#### Chat Streaming (`/api/[agentSlug]/chat`)

```typescript
// 800s timeout voor lange AI operaties
export const maxDuration = 800;

export const POST = async (req: NextRequest) => {
  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const result = streamText({
        model: openrouter(agent.config.model),
        system: promptWithContext,
        messages: convertToModelMessages(messages),
        tools: {
          /* AI tools */
        }
      });
      writer.merge(result.toUIMessageStream());
    }
  });
  return createUIMessageStreamResponse({ stream });
};
```

#### Authentication (`/api/auth/[...all]`)

```typescript
// Better Auth OAuth & session management
export const { GET, POST } = authServerClient.handler;
```

#### tRPC API (`/api/trpc/[trpc]`)

```typescript
// Type-safe RPC endpoints
export const { GET, POST } = trpcHandler({
  router: appRouter,
  createContext: createTRPCContext
});
```

## 🐛 Debugging & Development

### Key Debugging Points

#### Chat State Debugging

```typescript
// In ChatProvider - log chat state changes
useEffect(() => {
  console.log('Chat messages:', chat.messages);
  console.log('Chat status:', chat.status);
}, [chat.messages, chat.status]);
```

#### API Response Debugging

```typescript
// In API route - log tool executions
console.log('Tool called:', toolName, input);
console.log('Agent config:', agent.config);
console.log('Stream status:', result.status);
```

#### Database Query Debugging

```typescript
// Enable Drizzle logging
const db = drizzle(client, {
  logger: true // Logs all SQL queries
});
```

### Development Tools

#### Browser DevTools

- **Network Tab**: Monitor streaming responses
- **Console**: Check for React errors
- **React DevTools**: Inspect component state
- **Tanstack Query DevTools**: Monitor query cache

#### VS Code Extensions

- **Tailwind CSS IntelliSense**: Auto-complete classes
- **Prisma/Drizzle**: Database schema visualization
- **Thunder Client**: API testing

### Common Development Patterns

#### Error Boundaries

```typescript
// Wrap components for error catching
<ErrorBoundary fallback={<ErrorFallback />}>
  <ChatHistory />
</ErrorBoundary>
```

#### Loading States

```typescript
// Use Suspense for async components
<Suspense fallback={<ChatSkeleton />}>
  <ChatProvider agentSlug={agentSlug}>
    {children}
  </ChatProvider>
</Suspense>
```

## 🔒 Security Implementation

### Authentication Flow

```typescript
// Middleware pattern voor route protection
const user = await getCurrentUser(req.headers);
if (!user) {
  return new NextResponse('Unauthorized', { status: 401 });
}

// Agent access validation
if (chat.userId !== user.id) {
  return new NextResponse('Forbidden', { status: 403 });
}
```

### Environment Variable Security

```typescript
// Server-only environment access
import serverEnv from '@/server.env'; // ✅ Server component only
import clientEnv from '@/client.env'; // ✅ NEXT_PUBLIC_ only
```

### Input Validation

```typescript
// Zod schemas voor runtime validation
const inputSchema = z.object({
  message: z.string().max(10000),
  agentId: z.string().uuid()
});

const validated = inputSchema.parse(input);
```

### SQL Injection Prevention

```typescript
// Drizzle ORM prevents SQL injection
await db.select().from(users).where(eq(users.id, userId)); // ✅ Parameterized query
```

## 📊 Performance Monitoring

### Sentry Integration

- **Organization**: byont-ventures
- **Project**: apperto-ai-chat
- **Features**:
  - Automatic error tracking
  - Performance monitoring
  - Source map uploading
  - Vercel Cron monitoring
  - Browser request tunneling via `/monitoring`

### Metrics Tracked

- Response times
- Tool execution duration
- Message processing speed
- Error rates
- User engagement
- Web Vitals (LCP, CLS, FID)
- Database query performance

### Optimization Features

- **React Compiler** (babel-plugin-react-compiler v19.0.0-beta)
- **Turbo mode** voor development (`pnpm dev --turbo`)
- **Server-side rendering** met Next.js App Router
- **Code splitting** automatisch via Next.js
- **Image optimization** met Next.js Image en Sharp
- **React Suspense** voor lazy loading
- **Query prefetching** met Tanstack Query

### Optimization Tips

- Use React.memo voor expensive components
- Implement virtual scrolling voor lange chat histories
- Optimize chart rendering met Recharts canvas mode
- Cache frequently accessed data met React Query
- Gebruik `React.PropsWithChildren` ipv `React.FC`

## 🔄 Deployment

### Vercel Hosting

De applicatie wordt gehost op **Vercel** met de volgende integraties:

#### Production Deployment

- **Project**: `easylog-ai`
- **Team**: `easy-log`
- **Dashboard**: [https://vercel.com/easy-log/easylog-ai](https://vercel.com/easy-log/easylog-ai)
- **Monitoring Features**:
  - **Observability**: Edge Requests, Function Invocations, Error Rate tracking
  - **Analytics**: Web Vitals, user analytics (1 week retention)
  - **Speed Insights**: Performance metrics
  - **Firewall**: DDoS protection (24h logs)
  - **Logs**: Real-time logging
  - **AI Integration**: Vercel AI SDK support

#### Vercel Features

- **Automatic Deployments** via Git push
- **Preview Deployments** voor pull requests
- **Edge Functions** voor optimale performance
- **Vercel Blob Storage** voor file uploads
- **Vercel Cron Jobs** monitoring
- **Environment Variables** automatisch gesynchroniseerd
- **Deployment Protection** voor production
- **Skew Protection** voor API versioning
- **Fluid Compute** voor dynamische resources

#### Vercel-specifieke Environment Variables

```env
# Automatisch door Vercel ingesteld
NEXT_PUBLIC_VERCEL_URL="easylog-ai.vercel.app"
VERCEL_ENV="production" | "preview" | "development"
VERCEL_PROJECT_PRODUCTION_URL="easylog-ai.vercel.app"

# Vercel Blob Storage
BLOB_READ_WRITE_TOKEN="vercel_blob_..."
```

### Production Build

```bash
# Lokaal builden voor test
pnpm build

# Lokaal production server draaien
pnpm start

# Vercel deployment (automatisch via Git)
git push origin main
```

### Vercel CLI Deployment

```bash
# Installeer Vercel CLI
npm i -g vercel

# Link met bestaand project
vercel link --project=easylog-ai

# Deploy naar preview
vercel

# Deploy naar production
vercel --prod

# Check deployment status
vercel ls

# Bekijk logs
vercel logs easylog-ai.vercel.app
```

### Environment Specific Settings

```bash
# Production (Vercel)
NODE_ENV=production
VERCEL_ENV=production

# Preview (Vercel)
NODE_ENV=production
VERCEL_ENV=preview

# Development (lokaal)
NODE_ENV=development
```

### Monitoring & Analytics

- **Sentry** voor error tracking
  - Automatische source map upload
  - Vercel Cron monitoring
  - Performance tracking
- **Vercel Analytics** (Web Vitals)
  - LCP, CLS, FID metrics
  - Real User Monitoring
- **Vercel Speed Insights**
- Database query monitoring
- OpenRouter usage tracking

### Vercel Project Settings

```json
{
  "name": "easylog-ai",
  "team": "easy-log",
  "buildCommand": "pnpm build",
  "outputDirectory": ".next",
  "devCommand": "pnpm dev",
  "installCommand": "pnpm install",
  "framework": "nextjs",
  "nodeVersion": "18.x",
  "regions": ["iad1"],
  "functions": {
    "api/[agentSlug]/chat/route.ts": {
      "maxDuration": 800
    }
  }
}
```

### Trigger.dev Integration

- **Auto-sync** van Vercel environment variabelen
- Background jobs management
- Cron job scheduling

## 🆕 Upcoming Features

### Planned Enhancements

- [ ] Voice input/output support
- [ ] Multi-language support
- [ ] Advanced chart interactions
- [ ] File upload in chat
- [ ] Chat export functionality
- [ ] Collaborative chat sessions
- [ ] Advanced search filters

### Agent Enhancements

- [ ] Custom tool development UI
- [ ] Agent performance analytics
- [ ] A/B testing for prompts
- [ ] Advanced role-based permissions

## 📞 Support

### Development Team Contact

- **Lead Developer**: [Contact Info]
- **UI/UX**: [Contact Info]
- **Backend**: [Contact Info]

### Documentation Links

- [API Documentation](./api-docs.md)
- [Agent Configuration Guide](./client-agent-configuration.md)
- [OpenRouter Setup](./openrouter-configuration.md)

### Community

- [GitHub Issues](https://github.com/easylog/issues)
- [Discord Community](https://discord.gg/easylog)
- [Documentation Wiki](https://wiki.easylog.nl)

## 📂 Quick Reference - Belangrijke Bestanden

### Core Application Files

```
apps/web/src/
├── app/(routes)/api/[agentSlug]/chat/route.ts   # Main chat endpoint
├── app/_chats/components/ChatProvider.tsx        # Chat state management
├── database/schema.ts                            # Database schema
├── server.env.ts                                 # Server environment
├── lib/trpc/server.ts                           # tRPC configuration
└── lib/ai-providers/openrouter.ts               # AI provider setup
```

### Configuration Files

```
apps/web/
├── next.config.ts                                # Next.js config
├── trigger.config.ts                             # Background jobs
├── drizzle.config.ts                            # Database config
├── tailwind.config.ts                           # Styling config
└── tsconfig.json                                 # TypeScript config
```

## 💡 Belangrijke Notities

### Hosting & Infrastructure

- **Vercel Project**: [easylog-ai](https://vercel.com/easy-log/easylog-ai) (Team: easy-log)
- **Production URL**: https://easylog-ai.vercel.app
- **Vercel Blob Storage** voor file uploads en document storage
- **PostgreSQL Database** voor applicatie data
- **Weaviate Vector Database** voor knowledge base
- **Automatic Deployments** via Git push naar main branch
- **Preview Deployments** voor pull requests
- **Monitoring Dashboard**: Real-time observability, analytics, en logs

### Verschil met Python Backend

De webchat heeft zijn **eigen AI implementatie** en communiceert NIET direct met de Python agents:

- Gebruikt dezelfde OpenRouter API voor consistentie
- Eigen TypeScript tool implementaties
- Chat geschiedenis in PostgreSQL database
- Agent configuraties worden uit database geladen

### Database Schema

Hoofdtabellen:

- `users` - Gebruiker accounts
- `sessions` - Actieve sessies
- `agents` - AI agent configuraties
- `chats` - Chat conversaties
- `documents` - Geüploade documenten
- `accounts` - OAuth provider accounts

### Trigger.dev Jobs

- **v4-beta.26** voor background taken
- Document ingest processing
- Async file conversies

### Development Commands

#### Daily Development

```bash
pnpm dev                    # Start dev server (met Turbo)
pnpm build                  # Build voor production
pnpm lint                   # Run linter
pnpm type-check            # TypeScript validation
```

#### Database Management

```bash
pnpm studio                 # Drizzle Studio UI
pnpm db:push               # Push schema changes
pnpm db:generate           # Generate migrations
```

#### Code Generation

```bash
pnpm generate:easylog      # Generate EasyLog API client
```

#### Background Jobs

```bash
pnpm trigger:dev           # Trigger.dev dashboard
pnpm trigger:deploy        # Deploy jobs to production
```

---

**Laatste Update**: Januari 2025
**Versie**: 3.0.0 - Developer Edition
**Focus**: Code architectuur en development patterns voor ontwikkelaars
