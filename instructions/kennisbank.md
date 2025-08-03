# EasyLog Kennisbank Documentatie

## 📖 Overzicht

De EasyLog Kennisbank is een geavanceerd AI-powered document management systeem dat naadloos integreert met de webchat functionaliteit. Het systeem biedt intelligente document verwerking, automatische content extractie, AI-gestuurde samenvatting en contextuele zoekfunctionaliteit.

## 🏗️ Architectuur

### Agent-Scoped Document Management
- **Elke agent heeft eigen kennisbank** - Volledige isolatie tussen agents
- **User-based access control** - Gebruikers zien alleen documenten van hun agents
- **Database relaties** - Documenten gekoppeld via `agentId` foreign key

### Core Components
```
Knowledge Base Pipeline:
Upload → Processing → AI Analysis → Storage → Search
```

## 📊 Database Schema

### Documents Table
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT random(),
  name TEXT NOT NULL,                    -- Originele bestandsnaam
  path TEXT,                            -- Vercel Blob storage pad
  type document_type_enum DEFAULT 'unknown',  -- 'pdf', 'xlsx', 'unknown'
  summary TEXT,                         -- AI-gegenereerde samenvatting
  tags TEXT[] DEFAULT '{}',             -- AI-gegenereerde tags
  content JSONB,                        -- Geparseerde document inhoud
  status document_status_enum DEFAULT 'pending', -- Processing status
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Status Enums
```sql
-- Document Types
CREATE TYPE document_type_enum AS ENUM ('unknown', 'pdf', 'xlsx');

-- Processing Status
CREATE TYPE document_status_enum AS ENUM (
  'pending',     -- Wacht op verwerking
  'processing',  -- Bezig met verwerken
  'completed',   -- Succesvol verwerkt
  'failed'       -- Verwerking mislukt
);
```

## 📤 Document Upload Pipeline

### 1. Frontend Upload Interface

**DocumentsDropzone Component**
```typescript
// Specificaties:
- Drag & drop interface
- Max 50 bestanden tegelijk
- Max 50MB per bestand
- Ondersteunde formaten: PDF (.pdf), Excel (.xlsx)
- Real-time upload progress
- Error handling voor rejected files
```

**Upload Restrictions**
```typescript
const uploadConfig = {
  maxFiles: 50,
  maxSize: 50000000, // 50MB
  accept: {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
  }
};
```

### 2. API Upload Endpoint

**Route: `/api/[agentSlug]/documents/upload`**

**Upload Flow:**
1. **Authentication** - User verificatie
2. **Agent Resolution** - Agent lookup via slug/UUID
3. **Document Creation** - Database record (status: 'pending')
4. **Blob Upload** - Vercel Blob storage
5. **Path Update** - Document path bijwerken
6. **Background Job** - Processing job triggeren

```typescript
// Upload proces:
onBeforeGenerateToken: async (pathname) => {
  // 1. Authenticatie check
  const user = await getCurrentUser(request.headers);
  
  // 2. Document record aanmaken
  const [document] = await db.insert(documents).values({
    name: pathname.split('/').pop() ?? 'unknown',
    agentId: agent.id,
    type: 'unknown',
    status: 'pending'
  }).returning();
  
  // 3. Upload configuratie
  return {
    allowedContentTypes: ['application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    addRandomSuffix: true,
    tokenPayload: JSON.stringify({ documentId: document.id })
  };
}
```

## 🔄 Document Processing Pipeline

### Background Processing (Trigger.dev)

**Job Orchestration:**
```
Upload Complete → ingest-document-job → format-specific-processor → AI Analysis → Database Update
```

## 📊 Excel Bestand Verwerking - Complete Flow

### 🔄 Volledige Processing Pipeline

Hier is de complete mapping van hoe een Excel bestand wordt verwerkt in het EasyLog systeem:

### **Stap 1: Frontend Upload** 
```typescript
// User sleept Excel bestand naar DocumentsDropzone
File eigenschappen:
- Naam: "sales_data_2024.xlsx"
- Grootte: 2.3MB (onder 50MB limiet)
- MIME type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
- Validatie: ✅ PASSED
```

### **Stap 2: API Upload Endpoint**
```typescript
// POST /api/[agentSlug]/documents/upload
Process:
1. Authentication ✅
2. Agent lookup ✅
3. Database document record:
   {
     id: "doc-uuid-123",
     name: "sales_data_2024.xlsx",
     agentId: "agent-uuid-456", 
     type: "unknown",
     status: "pending",
     path: null,
     content: null,
     summary: null,
     tags: []
   }
```

### **Stap 3: Vercel Blob Upload**
```typescript
// File upload naar CDN
Blob properties:
- Path: "random-uuid/sales_data_2024.xlsx"
- Access: "public" 
- URL: "https://blob.vercel-storage.com/random-uuid/sales_data_2024.xlsx"
- Encryption: At-rest

// Database update:
UPDATE documents SET path = "random-uuid/sales_data_2024.xlsx" WHERE id = "doc-uuid-123"
```

### **Stap 4: Background Job Trigger**
```typescript
// Trigger.dev: ingest-document-job
Input: { documentId: "doc-uuid-123" }

Process:
1. Document ophalen uit database ✅
2. Vercel Blob HEAD request ✅  
3. Content-Type detectie: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ✅
4. Route naar process-xlsx-job ✅
```

### **Stap 5: Excel Processing (SheetJS)**
```typescript
// process-xlsx-job.ts execution
Input: { downloadUrl: "https://blob.vercel-storage.com/..." }

Processing Steps:
1. File download van Blob storage
2. ArrayBuffer conversie
3. XLSX.read(buffer, { type: 'buffer' })
4. Per worksheet processing:

// Voorbeeld output structuur:
[
  {
    sheetName: "Sales Q1",
    sheetIndex: 0,
    content: [
      { "Product": "Laptop", "Price": 999, "Quantity": 50, "Revenue": 49950 },
      { "Product": "Mouse", "Price": 25, "Quantity": 200, "Revenue": 5000 },
      { "Product": "Keyboard", "Price": 75, "Quantity": 100, "Revenue": 7500 }
    ]
  },
  {
    sheetName: "Sales Q2", 
    sheetIndex: 1,
    content: [
      { "Product": "Monitor", "Price": 299, "Quantity": 75, "Revenue": 22425 },
      { "Product": "Webcam", "Price": 89, "Quantity": 150, "Revenue": 13350 }
    ]
  }
]
```

### **Stap 6: AI Analysis (Google Gemini 2.5 Flash)**
```typescript
// AI Summarization van Excel data
Input: JSON.stringify(processingResult.output, null, 2)

AI Prompt Analysis:
"Act as a professional summarizer. Create a concise summary of the sales data below:
- Ensure summary includes relevant details
- Length within 1000 characters  
- Summary in English
- Generate tags for entities (products, categories, etc.)"

// Voorbeeld AI Response:
{
  summary: "Sales data spreadsheet containing Q1 and Q2 performance metrics for electronic products. Q1 includes laptops (50 units, $49,950), peripherals like mice (200 units, $5,000) and keyboards (100 units, $7,500). Q2 focuses on monitors (75 units, $22,425) and webcams (150 units, $13,350). Total revenue across quarters shows strong performance in laptop sales and growing peripheral market demand.",
  
  tags: ["sales", "electronics", "laptops", "peripherals", "Q1", "Q2", "revenue", "inventory", "products", "quarterly-data"]
}
```

### **Stap 7: Database Final Update**
```typescript
// Final document record update
UPDATE documents SET 
  type = 'xlsx',
  status = 'completed', 
  summary = 'Sales data spreadsheet containing Q1 and Q2 performance...',
  tags = ['sales', 'electronics', 'laptops', 'peripherals', 'Q1', 'Q2', 'revenue'],
  content = [
    {
      sheetName: "Sales Q1",
      sheetIndex: 0, 
      content: [...]
    },
    {
      sheetName: "Sales Q2",
      sheetIndex: 1,
      content: [...]  
    }
  ]
WHERE id = 'doc-uuid-123';
```

### **Stap 8: Knowledge Base Beschikbaarheid**

**Chat Search Integration:**
```typescript
// Als user vraagt: "What were our laptop sales in Q1?"

searchKnowledgeBase proces:
1. 🔍 Query database voor agent documenten
2. 📄 AI selecteert relevante documenten (sales_data_2024.xlsx)  
3. 🔬 Content extractie:
   - Sheet: "Sales Q1"
   - Find: Product = "Laptop"
   - Extract: "Laptop sales Q1: 50 units, $999 each, total revenue $49,950"
4. ✅ Return formatted result
```

**Knowledge Base Interface:**
```typescript
// /[agentSlug]/knowledge-base weergave:
Document List:
┌─────────────────────┬──────────┬─────────────┬─────────────────┐
│ Name                │ Type     │ Status      │ Created         │
├─────────────────────┼──────────┼─────────────┼─────────────────┤
│ sales_data_2024.xlsx│ xlsx     │ completed   │ 2024-01-15 14:30│
└─────────────────────┴──────────┴─────────────┴─────────────────┘

Tags: sales, electronics, laptops, peripherals, Q1, Q2, revenue
Summary: Sales data spreadsheet containing Q1 and Q2 performance...
```

### 📊 Data Transformatie Voorbeelden

#### **Excel Input → JSON Output**

**Original Excel Structure:**
```
Sheet: "Sales Q1"
┌─────────┬───────┬──────────┬─────────┐
│ Product │ Price │ Quantity │ Revenue │
├─────────┼───────┼──────────┼─────────┤
│ Laptop  │  999  │    50    │  49950  │
│ Mouse   │   25  │   200    │   5000  │
└─────────┴───────┴──────────┴─────────┘
```

**JSON Output in Database:**
```json
{
  "sheetName": "Sales Q1",
  "sheetIndex": 0,
  "content": [
    {
      "Product": "Laptop",
      "Price": 999,
      "Quantity": 50, 
      "Revenue": 49950
    },
    {
      "Product": "Mouse",
      "Price": 25,
      "Quantity": 200,
      "Revenue": 5000
    }
  ]
}
```

### 🔍 Excel Search & Query Capabilities

**Mogelijke Chat Queries:**
```typescript
// Voorbeeld vragen die beantwoord kunnen worden:
"What products did we sell in Q1?" 
→ Finds: Laptop, Mouse, Keyboard from Sales Q1 sheet

"Show me revenue by product"
→ Extracts: Revenue column per product across sheets

"What was our total Q2 performance?"  
→ Calculates: Sum of Revenue from Sales Q2 sheet

"Which quarter had better laptop sales?"
→ Compares: Laptop data between Q1 and Q2 sheets
```

### ⚡ Excel Processing Performance

**Processing Times:**
- **Small Excel** (< 1MB): ~10-15 seconden
- **Medium Excel** (1-10MB): ~30-60 seconden  
- **Large Excel** (10-50MB): ~2-5 minuten

**Optimization Features:**
- **SheetJS streaming** voor grote bestanden
- **Parallel sheet processing** waar mogelijk
- **JSON compression** in database
- **AI batch processing** voor multiple sheets

### 🔧 Excel Error Handling

**Mogelijke Issues & Oplossingen:**
```typescript
// Corrupt Excel file
→ SheetJS error → Status: 'failed' → User notification

// Extremely large file  
→ Timeout → Retry with smaller chunks → Status update

// AI service unavailable
→ Fallback: Store raw data → Retry summarization later

// Invalid Excel format
→ Format detection → Error message → Upload rejection
```

### 💾 Excel Storage Efficiency

**Data Opslag:**
- **Original file**: Vercel Blob (CDN, encrypted)
- **Parsed data**: PostgreSQL JSONB (indexed, queryable)
- **AI summary**: TEXT field (searchable)
- **Tags**: Array (indexed voor filtering)

**Query Performance:**
```sql
-- Efficient queries mogelijk:
SELECT * FROM documents WHERE 'sales' = ANY(tags);
SELECT * FROM documents WHERE content @> '{"sheetName": "Sales Q1"}';
SELECT * FROM documents WHERE summary ILIKE '%laptop%';
```

## 🔍 Intelligent Search System

### Search Tool: `toolSearchKnowledgeBase`

**AI-Powered Document Discovery:**
```typescript
// Search Pipeline:
1. Database Query (max 50 documenten)
2. AI Document Ranking (Google Gemini 2.5 Flash)
3. Relevance Analysis
4. Batch Content Extraction (3 parallel)
5. Human-Readable Formatting
```

### Search Intelligence

**Document Ranking Prompt:**
```typescript
const rankingPrompt = `
You are a document search assistant. Analyze the user's question and available documents to identify which documents are most relevant.

User Question: "${userSearchQuery}"

Available Documents:
${documents.map(doc => `${doc.id} (${doc.name}): ${doc.summary}`).join('\n')}

Consider:
- Direct relevance to question topic
- Whether document content would help answer query
- Specificity and usefulness of information

Return only genuinely helpful documents for answering the user's question.
`;
```

**Content Extraction:**
```typescript
const extractionPrompt = `
You are an expert information extractor. Given a user query and search result, extract all pieces of information relevant to answering the user's query.

Requirements:
- Return only relevant information as plain text
- Must be human readable
- No commentary or metadata
- Return empty string if no relevant information found
`;
```

### Real-Time Search Feedback

**Chat Integration:**
```typescript
// Status Updates tijdens search:
messageStreamWriter.write({
  type: 'data-document-search',
  id: searchId,
  data: {
    status: 'searching_documents',
    content: `Searching relevant knowledge base documents for "${query}"`
  }
});

// Status Flow:
'searching_documents' → 'documents_found' → 'researching_document' → 'document_research_complete'
```

**Visual Progress Indicators:**
- 🔍 **Searching documents...** - Database query actief
- 📄 **Documents found** - Relevante documenten geïdentificeerd
- 🔬 **Researching [document]: [reason]** - Content extractie bezig
- ✅ **Research complete** - Resultaten beschikbaar

## 🎯 Knowledge Base Management Interface

### Route: `/[agentSlug]/knowledge-base`

**Interface Components:**

### 1. DocumentsActionRow
```typescript
// Features:
- Upload knop met icon
- Dialog trigger voor upload modal
- Agent-scoped functionaliteit
```

### 2. DocumentsDataTable
```typescript
// Features:
- Infinite scrolling (100 documenten per pagina)
- Real-time data updates
- Status column (pending/processing/completed/failed)
- Created date sorting
- Agent isolation
```

### 3. DocumentsUploadDialog
```typescript
// Features:
- Modal interface
- Drag & drop zone
- Multiple file selection
- Progress tracking
- Error handling
- Success notifications
```

### Data Fetching Strategy

**Infinite Query Pattern:**
```typescript
const { data } = useSuspenseInfiniteQuery(
  api.documents.getMany.infiniteQueryOptions({
    cursor: 0,
    limit: 100,
    agentId: agentSlug
  }),
  {
    getNextPageParam: (lastPage, allPages) => {
      const total = allPages.reduce((acc, page) => acc + page.data.length, 0);
      return total >= lastPage.meta.total ? undefined : lastPage.meta.cursor + lastPage.meta.limit;
    }
  }
);
```

## 🧠 AI Chat Integration

### Available Tools

**1. searchKnowledgeBase**
```typescript
// Beschrijving: "Search the knowledge base for information"
// Input: userSearchQuery (string)
// Output: Relevant information from documents
// Real-time status updates
```

**2. loadDocument**
```typescript
// Beschrijving: "Load a document into the knowledge base"
// Input: documentId (string)
// Output: Complete document JSON
// Direct database access
```

**3. createChart**
```typescript
// Beschrijving: "Create a chart"
// Input: Chart configuration
// Output: Visual chart in chat
// Data visualization van document content
```

### Chat Message Types

**Document Search Messages:**
```typescript
// Schema:
const documentSearchSchema = z.object({
  status: z.enum([
    'searching_documents',
    'documents_found', 
    'researching_document',
    'document_research_complete'
  ]),
  content: z.string()
});
```

**Visual Components:**
- **ChatMessageAssistantDocumentSearch** - Status weergave
- **Progress indicators** - Real-time processing updates
- **Formatted results** - Structured information display

## 💾 Vector Database Integration (Future)

### Weaviate Setup

**Collection Schema:**
```typescript
const documentCollection = {
  name: 'Document',
  vectorizers: vectorizer.text2VecOpenAI(),
  properties: [
    { name: 'filename', dataType: dataType.TEXT },
    { name: 'organizationId', dataType: dataType.UUID },
    { name: 'summary', dataType: dataType.TEXT },
    { name: 'tags', dataType: dataType.TEXT_ARRAY }
  ]
};
```

**Benefits (When Implemented):**
- **Semantic search** - Meaning-based document discovery
- **Vector similarity** - Related document suggestions
- **Advanced relevance** - Better than keyword matching
- **Scalable search** - Efficient voor grote document sets

## 🚀 Performance Optimizations

### Processing Optimizations
- **Batch processing** - 3 documenten parallel tijdens search
- **Streaming responses** - Real-time status updates
- **Efficient queries** - Database indexing op agentId
- **CDN storage** - Vercel Blob voor snelle access

### Search Optimizations
- **Document limit** - Max 50 documenten per search (performance)
- **AI model selection** - Gemini 2.5 Flash (snelheid/kwaliteit balance)
- **Caching strategy** - Query result caching
- **Progressive results** - Resultaten tonen tijdens processing

### Database Optimizations
```sql
-- Recommended indexes:
CREATE INDEX idx_documents_agent_id ON documents(agent_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_documents_agent_status ON documents(agent_id, status);
```

## 🔒 Security & Compliance

### Access Control
- **Authentication required** - Alle endpoints beveiligd
- **Agent isolation** - Users zien alleen eigen agent documenten
- **Role-based access** - Agent-specific permissions
- **Audit trail** - Created/updated timestamps

### Data Protection
- **Encrypted storage** - Vercel Blob encryption
- **HIPAA compliance ready** - Voor healthcare agents
- **No data leakage** - Strict agent boundaries
- **Secure processing** - Background jobs isolated

### File Security
- **Content type validation** - Strict MIME type checking
- **File size limits** - 50MB maximum
- **Virus scanning** - Ready for integration
- **Access logs** - Monitoring en tracking

## 🐛 Error Handling & Monitoring

### Error Types & Solutions

**Upload Errors:**
```typescript
// Common issues:
- File too large (>50MB) → User feedback
- Unsupported format → Clear error message  
- Network timeout → Retry mechanism
- Authentication failure → Redirect to login
```

**Processing Errors:**
```typescript
// Background job failures:
- OCR failure → Status: 'failed', retry job
- AI service timeout → Exponential backoff
- Storage failure → Cleanup + retry
- Invalid content → Mark as failed
```

**Search Errors:**
```typescript
// Search failures:
- No documents found → Empty state message
- AI service unavailable → Fallback search
- Database timeout → Error message + retry
- Permission denied → Access control message
```

### Monitoring & Observability

**Sentry Integration:**
```typescript
// Error tracking:
- Upload failures
- Processing job errors
- Search timeouts
- Authentication issues
- Performance metrics
```

**Logging Strategy:**
```typescript
// Log levels:
- INFO: Successful operations
- WARN: Recoverable issues  
- ERROR: Failed operations
- DEBUG: Detailed processing info
```

## 📈 Analytics & Metrics

### Key Performance Indicators

**Upload Metrics:**
- Upload success rate
- Average file size
- Processing time per document type
- Failed upload reasons

**Search Metrics:**
- Search query frequency
- Average response time
- Document relevance scores
- User satisfaction (implicit)

**Processing Metrics:**
- OCR accuracy rates
- AI summarization quality
- Background job completion times
- Error rates by document type

### Usage Analytics
```typescript
// Trackable events:
- Document uploads per agent
- Search queries per user
- Most accessed documents
- Processing time trends
- Popular document types
```

## 🆕 Future Enhancements

### Planned Features

**Short Term (Q1-Q2 2024):**
- [ ] **Vector search** - Weaviate integration activeren
- [ ] **Document versioning** - Multiple versions per document
- [ ] **Bulk operations** - Mass upload/delete functionality
- [ ] **Advanced filters** - Filter op tags, date, type
- [ ] **Document preview** - In-chat document viewing

**Medium Term (Q3-Q4 2024):**
- [ ] **Multi-language support** - Documenten in verschillende talen
- [ ] **OCR improvements** - Handwriting recognition
- [ ] **Collaborative features** - Document sharing tussen agents
- [ ] **API access** - REST API voor externe integraties
- [ ] **Webhook notifications** - Processing status updates

**Long Term (2025+):**
- [ ] **Advanced AI models** - GPT-4V voor image understanding
- [ ] **Real-time collaboration** - Live document editing
- [ ] **Enterprise features** - SSO, audit logs, compliance
- [ ] **Mobile optimization** - Native mobile upload
- [ ] **Voice processing** - Audio document transcription

### Technical Improvements

**Performance:**
- **Incremental processing** - Delta updates voor grote documenten
- **Smart caching** - Redis integration voor search results
- **Background sync** - Offline processing queue
- **CDN optimization** - Global content delivery

**User Experience:**
- **Progressive web app** - Offline functionality
- **Keyboard shortcuts** - Power user features
- **Batch actions** - Multiple document operations
- **Smart suggestions** - AI-powered search suggestions

## 🔧 Development Guidelines

### Adding New Document Types

**1. Update Schema:**
```sql
-- Add new type to enum
ALTER TYPE document_type_enum ADD VALUE 'new_type';
```

**2. Create Processor:**
```typescript
// New processor job
export const processNewTypeJob = schemaTask({
  id: 'process-new-type',
  schema: z.object({
    downloadUrl: z.string()
  }),
  run: async ({ downloadUrl }) => {
    // Processing logic
    return processedContent;
  }
});
```

**3. Update Ingest Job:**
```typescript
// Add to content type mapping
const supportedContentTypes = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'new/mime-type' // Add new type
];
```

**4. Update Frontend:**
```typescript
// Add to upload restrictions
accept: {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'new/mime-type': ['.ext'] // Add new extension
}
```

### Extending Search Capabilities

**Custom Search Tools:**
```typescript
// New search tool
const toolCustomSearch = () => tool({
  description: 'Custom search functionality',
  inputSchema: z.object({
    query: z.string(),
    filters: z.object({
      documentType: z.string().optional(),
      dateRange: z.object({
        from: z.date(),
        to: z.date()
      }).optional()
    }).optional()
  }),
  execute: async ({ query, filters }) => {
    // Custom search logic
  }
});
```

### Testing Strategy

**Unit Tests:**
- Document upload validation
- Processing job logic
- Search algorithm accuracy
- Error handling scenarios

**Integration Tests:**
- End-to-end upload pipeline
- AI service integration
- Database operations
- Chat tool functionality

**Performance Tests:**
- Large file processing
- Concurrent upload handling
- Search response times
- Database query optimization

## 📞 Support & Troubleshooting

### Common Issues

**"Documents not showing up"**
```bash
# Check agent ID matching
# Verify user permissions
# Check database constraints
# Review error logs
```

**"Upload fails consistently"**
```bash
# Check file size (50MB limit)
# Verify supported formats (PDF/XLSX)
# Test network connectivity
# Review Vercel Blob configuration
```

**"Search returns no results"**
```bash
# Verify documents are processed (status: 'completed')
# Check AI service availability
# Review search query format
# Test with known document content
```

**"Processing stuck in 'processing' status"**
```bash
# Check Trigger.dev job logs
# Verify AI service limits
# Review background job queue
# Test with smaller documents
```

### Debug Commands

```bash
# Check document status
SELECT id, name, status, created_at FROM documents WHERE agent_id = 'agent-uuid';

# Monitor processing jobs
# Check Trigger.dev dashboard

# Test search functionality
# Use chat interface with simple queries

# Verify blob storage
# Check Vercel dashboard for uploaded files
```

### Contact & Support

**Development Team:**
- **Backend**: Document processing pipeline
- **AI Integration**: Search & summarization
- **Frontend**: Upload interface & chat integration
- **DevOps**: Infrastructure & monitoring

**Documentation:**
- [Upload API Reference](./api-upload.md)
- [Search Tool Documentation](./search-tools.md)
- [Processing Pipeline Guide](./processing-guide.md)
- [Troubleshooting Guide](./troubleshooting.md)

---

**Laatste Update**: Januari 2024  
**Versie**: 2.0.0  
**Status**: Production Ready ✅

**Belangrijke Links:**
- [Webchat Instructies](./webchat-instructies.md)
- [Agent Configuratie](./client-agent-configuration.md)
- [OpenRouter Setup](./openrouter-configuration.md)