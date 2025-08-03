# EasyLog Webchat Instructies

## 📖 Overzicht

De EasyLog Webchat is een geavanceerde Next.js applicatie die naadloos integreert met het EasyLog Agent systeem. Het biedt een rijke, interactieve chat interface voor AI agents met uitgebreide tool capabilities, real-time visualisaties en document search functionaliteit.

## 🏗️ Technische Architectuur

### Core Technologies
- **Next.js 15** met App Router
- **React 18** met hooks en context patterns
- **TypeScript** voor complete type safety
- **Tailwind CSS** voor responsive styling
- **Framer Motion** voor smooth animaties
- **tRPC** voor type-safe API communicatie
- **AI SDK** (`@ai-sdk/react`) voor streaming chat functionaliteit
- **Drizzle ORM** voor database operaties
- **Zod** voor runtime validation

### Backend Integration
- **OpenRouter** voor AI model access (300+ modellen)
- **Agent-specifieke configuratie** via JSON configs
- **Real-time streaming** responses
- **Tool orchestration** met async execution

## 🚀 Installatie en Setup

### Prerequisites
```bash
# Node.js 18+ required
node --version

# pnpm als package manager
npm install -g pnpm
```

### Development Setup
```bash
# Navigate to web app
cd apps/web

# Install dependencies
pnpm install

# Setup environment variables
cp .env.example .env.local

# Run database migrations
pnpm db:migrate

# Start development server
pnpm dev
```

### Environment Variables
```env
# Database
DATABASE_URL="postgresql://..."

# AI Providers
OPENROUTER_API_KEY="sk-or-..."

# Authentication
NEXTAUTH_SECRET="..."
NEXTAUTH_URL="http://localhost:3000"

# EasyLog Backend API
EASYLOG_API_URL="https://api.easylog.nl"
EASYLOG_API_TOKEN="..."
```

## 🎯 Gebruiksinstructies

### Agent Toegang
1. **Navigeer naar agent**: `/[agentSlug]/chat`
2. **Authenticatie**: Inloggen via EasyLog credentials
3. **Chat starten**: Type bericht en druk Enter

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

## 🔧 API Endpoints

### Chat API (`/api/[agentSlug]/chat`)
**Method**: POST
**Timeout**: 800 seconds
**Authentication**: Required

**Request Body**:
```typescript
{
  message: UIMessage,
  id: string // Chat ID
}
```

**Response**: Streaming AI response with tool executions

### Agent Routes
- `/[agentSlug]/chat` - Main chat interface
- `/[agentSlug]/knowledge-base` - Document management
- `/api/[agentSlug]/documents` - Document operations

## 🐛 Troubleshooting

### Common Issues

**Chat Not Loading**
```bash
# Check agent configuration
# Verify database connection
# Check OpenRouter API key
```

**Tools Not Working**
- Verify agent has tool permissions
- Check API credentials
- Review error logs in browser console

**Streaming Issues**
- Check network connection
- Verify API timeout settings
- Review server logs

**Performance Issues**
- Monitor message history size
- Check for memory leaks in React components
- Review network requests in DevTools

### Debug Mode
```bash
# Enable debug logging
NODE_ENV=development pnpm dev

# Check agent logs
tail -f logs/agent.log

# Monitor database queries
DRIZZLE_DEBUG=true pnpm dev
```

### Error Handling
```typescript
// Component error boundaries are implemented
// Check browser console for detailed errors
// Server errors logged to console/files
```

## 🔒 Security Considerations

### Authentication
- All routes require valid user session
- Agent access controlled per user
- JWT tokens with expiration

### Data Protection
- HIPAA compliance for healthcare agents
- No sensitive data in client-side logs
- Encrypted API communications

### Rate Limiting
- Per-user chat limits
- API rate limiting via OpenRouter
- Database connection pooling

## 📊 Performance Monitoring

### Metrics Tracked
- Response times
- Tool execution duration
- Message processing speed
- Error rates
- User engagement

### Optimization Tips
- Use React.memo for expensive components
- Implement virtual scrolling for long chat histories
- Optimize chart rendering with canvas
- Cache frequently accessed data

## 🔄 Deployment

### Production Build
```bash
# Build application
pnpm build

# Run production server
pnpm start
```

### Environment Specific Settings
```bash
# Production
NODE_ENV=production

# Staging
NODE_ENV=staging

# Development
NODE_ENV=development
```

### Monitoring
- Sentry for error tracking
- Performance monitoring via Web Vitals
- Database query monitoring
- OpenRouter usage tracking

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

---

**Laatste Update**: Januari 2024
**Versie**: 2.0.0
**Status**: Production Ready ✅