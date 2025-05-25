# OpenRouter Configuration Documentation

## Overview

OpenRouter serves as the unified LLM interface for the EasyLog Python server project, providing access to 300+ AI models from various providers through a single API. The system is configured to use OpenRouter as the primary gateway for all LLM interactions, offering better pricing, uptime, and model variety compared to direct provider integrations.

## Architecture Integration

### Core Configuration

**Primary Configuration File**: `apps/api/src/lib/openai.py`

```python
from openai import AsyncOpenAI
from src.settings import settings

openai_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)
```

**Settings Configuration**: `apps/api/src/settings.py`

```python
class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    MISTRAL_API_KEY: str      # Additional API key (unused in current setup)
    OPENAI_API_KEY: str       # Additional API key (unused in current setup)
    # ... other settings
```

### Environment Variables

**Required Environment Variables**:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

**Optional Environment Variables**:

```bash
MISTRAL_API_KEY=your_mistral_key      # For future direct integration
OPENAI_API_KEY=your_openai_key        # For future direct integration
```

## Available Models

### Current Agent Configurations

#### MUMCAgent & EasyLogAgent

- **Default Model**: `anthropic/claude-sonnet-4`
- **Use Case**: Advanced reasoning, medical analysis, complex business logic
- **Cost**: Premium tier for high-quality responses

#### DebugAgent & RETAgent

- **Default Model**: `openai/gpt-4.1`
- **Use Case**: Development, debugging, general assistance
- **Cost**: Balanced performance and cost

#### RickThropicAgent

- **Default Model**: `openai/gpt-4.1`
- **Use Case**: Experimental features, knowledge graph integration
- **Cost**: Standard pricing

### Model Categories Available

#### OpenAI Models

- **GPT-4.1**: Latest flagship model (1M context, $2/M input, $8/M output)
- **GPT-4.1 Mini**: Mid-sized performance ($0.40/M input, $1.60/M output)
- **GPT-4.1 Nano**: Fastest, cheapest ($0.10/M input, $0.40/M output)
- **GPT-4o**: Vision and multimodal capabilities ($2.50/M input, $10/M output)
- **GPT-4o-mini**: Cost-effective multimodal ($0.15/M input, $0.60/M output)
- **o1 Series**: Reasoning models ($15-150/M input, enhanced thinking)

#### Anthropic Models

- **Claude Sonnet 4**: Premium reasoning (1.1B tokens/week usage)
- **Claude 3.7 Sonnet**: High-performance alternative
- **Claude 3 Haiku**: Fast, cost-effective option

#### Other Available Providers

- **Mistral**: `mistralai/mistral-small-3.1-24b-instruct` ($0.05/M input)
- **Meta Llama**: Various Llama 3.1 variants
- **Google**: Gemini Pro models
- **Qwen**: High-performance Chinese models
- **DeepSeek**: Code-specialized models

### Model Selection Guidelines

#### For Medical/Health Applications (MUMC)

```python
# Primary: Advanced reasoning and safety
"anthropic/claude-sonnet-4"

# Alternative: Cost-effective with good performance
"anthropic/claude-3.7-sonnet"

# Budget option: Still high quality
"openai/gpt-4.1-mini"
```

#### For Business/Planning Applications (EasyLog)

```python
# Complex analysis and planning
"anthropic/claude-sonnet-4"

# Data analysis and SQL generation
"openai/gpt-4.1"

# High-volume operations
"openai/gpt-4.1-nano"
```

#### For Development/Debugging

```python
# Code generation and debugging
"openai/gpt-4.1"

# Code reasoning and complex logic
"openai/o1-mini"

# Fast iterations and testing
"openai/gpt-4o-mini"
```

## Implementation Patterns

### Model Configuration in Agents

**Role-Based Model Selection**:

```python
class RoleConfig(BaseModel):
    name: str = Field(default="AssistantRole")
    prompt: str = Field(default="System prompt...")
    model: str = Field(
        default="anthropic/claude-sonnet-4",
        description="Model ID from https://openrouter.ai/models"
    )
    tools_regex: str = Field(default=".*")
    allowed_subjects: list[str] | None = Field(default=None)
```

**Dynamic Model Switching**:

```python
# In agent implementation
async def on_message(self, messages) -> tuple[...]:
    role_config = await self.get_current_role()

    # Use role-specific model
    response = await self.client.chat.completions.create(
        model=role_config.model,  # OpenRouter model ID
        messages=[...],
        stream=True,
        tools=[...],
    )
```

### OpenAI SDK Compatibility

OpenRouter maintains full OpenAI SDK compatibility:

```python
from openai import AsyncOpenAI

# Works exactly like OpenAI client
client = AsyncOpenAI(
    api_key="your_openrouter_key",
    base_url="https://openrouter.ai/api/v1"
)

# Standard OpenAI API calls work unchanged
response = await client.chat.completions.create(
    model="anthropic/claude-sonnet-4",  # Any OpenRouter model
    messages=[{"role": "user", "content": "Hello"}],
    stream=True
)
```

### Error Handling and Fallbacks

OpenRouter provides automatic provider routing and fallbacks:

```python
# OpenRouter handles provider failures automatically
# No additional error handling needed for provider outages
try:
    response = await client.chat.completions.create(
        model="anthropic/claude-sonnet-4",
        messages=messages
    )
except Exception as e:
    # Handle rate limits, invalid requests, etc.
    logger.error(f"OpenRouter error: {e}")
```

## Service Integrations

### Graphiti Knowledge Graph

**Configuration**: `apps/api/src/main.py`

```python
graphiti_lib.graphiti_connection = Graphiti(
    user=settings.NEO4J_USER,
    password=settings.NEO4J_PASSWORD,
    uri=settings.NEO4J_URI,
    llm_client=OpenAIClient(
        config=LLMConfig(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            model="openai/gpt-4.1-mini",  # Optimized for knowledge processing
        ),
        client=openai_client,
    ),
)
```

### Weaviate Vector Database

Weaviate uses OpenAI embeddings through OpenRouter for document indexing:

```python
# Weaviate configuration with OpenRouter
weaviate.classes.config.Configure.Vectorizer.text2vec_openai()
```

## Cost Management

### Model Pricing Tiers

#### Budget Tier ($0.10 - $0.60 per M tokens)

- `openai/gpt-4.1-nano`
- `openai/gpt-4o-mini`
- `mistralai/mistral-small-3.1-24b-instruct`

#### Standard Tier ($1.50 - $4.40 per M tokens)

- `openai/gpt-4.1-mini`
- `openai/o1-mini`
- `anthropic/claude-3-haiku`

#### Premium Tier ($8+ per M tokens)

- `openai/gpt-4.1`
- `anthropic/claude-sonnet-4`
- `openai/o1`

### Cost Optimization Strategies

1. **Model Selection by Use Case**:

   - Simple tasks: Use nano/mini models
   - Complex reasoning: Use premium models
   - Bulk processing: Use budget tier

2. **Context Window Management**:

   - Trim unnecessary context to reduce input tokens
   - Use appropriate context lengths per model

3. **Caching and Efficiency**:
   - Cache frequent queries when possible
   - Use streaming for real-time responses

## Security Configuration

### API Key Management

**Environment Variables Only**:

```bash
# .env file (ignored by git)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxx
```

**Docker Configuration**:

```yaml
# docker-compose.yaml
services:
  api:
    env_file:
      - .env # Contains OPENROUTER_API_KEY
```

### Data Privacy

OpenRouter provides configurable data policies:

- No training data usage by default
- Request/response logging can be disabled
- Provider-specific privacy controls available

## Monitoring and Analytics

### Usage Tracking

OpenRouter provides built-in analytics:

- Token usage per model
- Cost tracking
- Performance metrics
- Error rates by provider

### Application Visibility

Optional headers for tracking:

```python
# In agent requests (already implemented)
headers = {
    "HTTP-Referer": "https://your-app.com",
    "X-Title": "EasyLog Python Server"
}
```

## Model-Specific Features

### Tool Calling Support

Models with tool/function calling:

```python
# Supported models
TOOL_CALLING_MODELS = [
    "openai/gpt-4.1",
    "openai/gpt-4.1-mini",
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4",
    "openai/o1-mini"
]
```

### Vision Capabilities

Models with image processing:

```python
# Vision-enabled models
VISION_MODELS = [
    "openai/gpt-4o",
    "openai/gpt-4.1",
    "openai/gpt-4-vision-preview"
]
```

### Large Context Windows

Models for document processing:

```python
# High-context models
LARGE_CONTEXT_MODELS = [
    "openai/gpt-4.1",        # 1M tokens
    "openai/gpt-4.1-mini",   # 1M tokens
    "anthropic/claude-sonnet-4"  # 200K tokens
]
```

## Configuration Best Practices

### Development Environment

```python
# For development/testing
DEFAULT_DEV_MODEL = "openai/gpt-4.1-mini"  # Cost-effective
DEBUG_MODEL = "openai/gpt-4o-mini"         # Fast iterations
```

### Production Environment

```python
# For production workloads
DEFAULT_PROD_MODEL = "anthropic/claude-sonnet-4"  # High quality
FALLBACK_MODEL = "openai/gpt-4.1"                # Reliable alternative
```

### Role-Specific Optimization

```python
# Medical/Health roles
MEDICAL_MODEL = "anthropic/claude-sonnet-4"  # Safety-critical

# Business/Analytics roles
BUSINESS_MODEL = "openai/gpt-4.1"           # Structured reasoning

# Development/Debug roles
DEV_MODEL = "openai/gpt-4.1-mini"          # Fast and cost-effective
```

## Troubleshooting

### Common Issues

1. **Invalid Model Names**:

   - Check https://openrouter.ai/models for current model IDs
   - Ensure correct provider prefix (e.g., `anthropic/`, `openai/`)

2. **Rate Limiting**:

   - Monitor usage on OpenRouter dashboard
   - Implement exponential backoff for retries
   - Consider model distribution across providers

3. **Authentication Errors**:

   - Verify OPENROUTER_API_KEY in environment
   - Check API key permissions and credits

4. **Model Availability**:
   - Some models may be temporarily unavailable
   - OpenRouter automatically routes to available providers
   - Monitor model status on OpenRouter platform

### Debug Commands

```bash
# Check environment configuration
echo $OPENROUTER_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# View application logs
docker logs -f easylog-python-server.api
```

## Super Agent System

### Overview

The Super Agent is an autonomous background system that runs scheduled tasks at configurable intervals. It operates independently of user interactions and is designed for system maintenance, notifications, data processing, and automated workflows.

### Architecture

**Base Configuration**:

```python
@staticmethod
def super_agent_config() -> SuperAgentConfig[EasyLogAgentConfig] | None:
    return SuperAgentConfig(
        interval_seconds=10800,  # 3 hours (configurable)
        agent_config=EasyLogAgentConfig(),
    )
```

**Implementation Pattern**:

```python
async def on_super_agent_call(
    self, messages: Iterable[ChatCompletionMessageParam]
) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]] | None:
    # Define available tools for this super agent run
    tools = [
        BaseTools.tool_noop,           # Required: No-operation fallback
        # Add specific tools for your use case
    ]

    # Build context-specific prompt
    prompt = "Your super agent instructions here..."

    # Execute with specified model and tools
    response = await self.client.chat.completions.create(
        model="anthropic/claude-sonnet-4",  # Choose appropriate model
        messages=[{"role": "system", "content": prompt}],
        stream=True,
        tools=[function_to_openai_tool(tool) for tool in tools],
        tool_choice="auto",
    )

    return response, tools
```

### Current Use Cases

#### 1. Notification Management System (EasyLogAgent)

**Purpose**: Automatically send due reminders and scheduled notifications
**Frequency**: Every 3 hours (`interval_seconds=10800`)
**Model**: `anthropic/claude-sonnet-4`
**Tools Used**:

- `tool_send_notification`: Send push notifications
- `tool_noop`: Skip when no notifications needed

**Features**:

- Evaluates pending reminders based on due dates
- Processes recurring tasks using cron expressions
- Prevents duplicate notifications
- Operates silently (no user-visible output)
- Returns response for external handling

#### 1b. Notification Management System (DebugAgent)

**Purpose**: Development/testing version of notification management
**Frequency**: Every 2 hours (`interval_seconds=60 * 60 * 2`)
**Model**: `openai/gpt-4.1`
**Tools Used**:

- `tool_send_notification`: Send push notifications
- `tool_noop`: Skip when no notifications needed

**Features**:

- Same notification logic as EasyLogAgent
- Enhanced logging with response details
- Handles completion internally with `_handle_completion`
- Development-optimized for faster iterations

**Key Implementation Difference**:

```python
# DebugAgent handles completion internally
async for _ in self._handle_completion(response, tools, messages):
    pass

# EasyLogAgent returns response for external handling
return response, tools
```

#### 2. System Monitoring (Extensible)

**Potential Purpose**: Health checks, performance monitoring
**Tools Needed**:

- Database health checks
- API endpoint monitoring
- Resource usage alerts

### Current Agent Super Agent Configurations

Here's a comprehensive overview of Super Agent implementations across different agent types:

| Agent            | Interval               | Model                       | Purpose                            | Tools                                   | Implementation Style                   |
| ---------------- | ---------------------- | --------------------------- | ---------------------------------- | --------------------------------------- | -------------------------------------- |
| **EasyLogAgent** | 3 hours<br>`10800` sec | `anthropic/claude-sonnet-4` | Production notification management | `tool_send_notification`<br>`tool_noop` | Returns response for external handling |
| **DebugAgent**   | 2 hours<br>`7200` sec  | `openai/gpt-4.1`            | Development/testing notifications  | `tool_send_notification`<br>`tool_noop` | Handles completion internally          |
| **MUMCAgent**    | 3 hours<br>`10800` sec | `anthropic/claude-sonnet-4` | Medical/health notifications       | `tool_send_notification`<br>`tool_noop` | Returns response for external handling |

#### Agent-Specific Super Agent Features

**EasyLogAgent & MUMCAgent (Production)**:

```python
@staticmethod
def super_agent_config() -> SuperAgentConfig[EasyLogAgentConfig] | None:
    return SuperAgentConfig(
        interval_seconds=10800,  # 3 hours
        agent_config=EasyLogAgentConfig(),
    )

# Returns response for framework handling
return response, tools
```

**DebugAgent (Development)**:

```python
@staticmethod
def super_agent_config() -> SuperAgentConfig[DebugAgentConfig] | None:
    return SuperAgentConfig(
        interval_seconds=60 * 60 * 2,  # 2 hours
        agent_config=DebugAgentConfig(),
    )

# Handles completion internally with enhanced logging
self.logger.info(f"Super agent response: {response.choices[0].message}")
async for _ in self._handle_completion(response, tools, messages):
    pass
```

### Configuration Options

#### Interval Settings

```python
# Quick intervals for active monitoring
interval_seconds=300     # 5 minutes

# Standard intervals for regular tasks
interval_seconds=1800    # 30 minutes
interval_seconds=3600    # 1 hour
interval_seconds=10800   # 3 hours (current default)

# Long intervals for maintenance tasks
interval_seconds=86400   # 24 hours
interval_seconds=604800  # 1 week
```

#### Model Selection for Different Tasks

```python
# Lightweight tasks (notifications, simple checks)
"openai/gpt-4.1-nano"         # Cost-effective for simple logic

# Standard tasks (data processing, analysis)
"openai/gpt-4.1-mini"         # Balanced performance

# Complex tasks (reasoning, decision making)
"anthropic/claude-sonnet-4"   # High-quality reasoning

# Specialized tasks (code generation, debugging)
"openai/o1-mini"              # Enhanced reasoning for complex logic
```

### Tool Categories for Super Agent

#### System Management Tools

```python
# Database maintenance
tool_cleanup_old_data
tool_optimize_database
tool_backup_database

# File system management
tool_cleanup_temp_files
tool_rotate_logs
tool_compress_archives
```

#### Monitoring and Analytics Tools

```python
# Performance monitoring
tool_check_system_health
tool_monitor_api_endpoints
tool_track_usage_metrics

# Data analysis
tool_generate_usage_reports
tool_analyze_user_patterns
tool_detect_anomalies
```

#### Communication Tools

```python
# Notifications and alerts
tool_send_notification        # Already implemented
tool_send_email_alert
tool_post_to_slack
tool_update_dashboard

# User engagement
tool_send_reminder
tool_trigger_workflows
tool_schedule_follow_ups
```

#### Data Processing Tools

```python
# ETL operations
tool_process_incoming_data
tool_sync_external_apis
tool_update_search_indices

# Content management
tool_update_knowledge_base
tool_refresh_cached_data
tool_process_uploaded_files
```

### Use Case Examples

#### 1. Daily Health Check System

```python
async def on_super_agent_call(self, messages):
    tools = [
        BaseTools.tool_noop,
        tool_check_database_health,
        tool_verify_api_endpoints,
        tool_send_notification,
    ]

    prompt = """
    # Daily System Health Check

    Perform comprehensive health checks:
    1. Check database connectivity and performance
    2. Verify all API endpoints are responding
    3. Monitor resource usage (memory, CPU, disk)
    4. Send alerts if any issues found
    5. Generate daily health report

    If all systems are healthy, use tool_noop.
    If issues found, send notification with details.
    """
```

#### 2. Weekly Data Processing Pipeline

```python
async def on_super_agent_call(self, messages):
    tools = [
        BaseTools.tool_noop,
        tool_process_weekly_analytics,
        tool_update_user_insights,
        tool_generate_reports,
        tool_send_notification,
    ]

    prompt = """
    # Weekly Data Processing Pipeline

    Execute weekly data processing tasks:
    1. Aggregate user activity data from past week
    2. Generate insights and patterns
    3. Update user recommendation models
    4. Create executive summary reports
    5. Notify stakeholders when complete
    """
```

#### 3. Content Maintenance System

```python
async def on_super_agent_call(self, messages):
    tools = [
        BaseTools.tool_noop,
        tool_refresh_knowledge_base,
        tool_update_search_indices,
        tool_cleanup_old_content,
        tool_send_notification,
    ]

    prompt = """
    # Content Maintenance System

    Maintain content freshness and quality:
    1. Refresh knowledge base from external sources
    2. Update search indices for better discovery
    3. Remove outdated or irrelevant content
    4. Optimize content for better user experience
    """
```

### Implementation Guidelines

#### 1. Design Principles

- **Autonomous Operation**: Should work without user intervention
- **Idempotent**: Safe to run multiple times
- **Error Handling**: Graceful failure and recovery
- **Logging**: Comprehensive logging for debugging
- **Resource Efficient**: Minimal resource consumption

#### 2. Best Practices

```python
# Always include tool_noop for fallback
tools = [BaseTools.tool_noop, ...other_tools]

# Use appropriate model for task complexity
model = "openai/gpt-4.1-nano"  # For simple tasks
model = "anthropic/claude-sonnet-4"  # For complex reasoning

# Include clear success/failure criteria
prompt = """
...
## Required Action
Take exactly ONE of these actions:
- If [condition]: invoke [specific_tool]
- If no action needed: invoke tool_noop

## IMPORTANT: OUTPUT RULES
- DO NOT provide text explanations
- ONLY call the appropriate tool
- This is a background process
"""
```

#### 3. Error Handling Strategy

```python
# In super agent implementation
try:
    # Super agent execution
    response = await self.client.chat.completions.create(...)
    return response, tools
except Exception as e:
    # Log error but don't crash the system
    self.logger.error(f"Super agent error: {e}")
    # Return None to skip this execution
    return None
```

### Scheduling and Coordination

#### Multiple Super Agent Instances

```python
# Different agents can have different intervals
class MaintenanceAgent(BaseAgent):
    @staticmethod
    def super_agent_config():
        return SuperAgentConfig(
            interval_seconds=86400,  # Daily maintenance
            agent_config=MaintenanceAgentConfig(),
        )

class MonitoringAgent(BaseAgent):
    @staticmethod
    def super_agent_config():
        return SuperAgentConfig(
            interval_seconds=300,   # Every 5 minutes
            agent_config=MonitoringAgentConfig(),
        )
```

#### Time-Based Coordination

```python
# Use current time for coordination
current_time = datetime.now()
current_hour = current_time.hour
current_day = current_time.weekday()

prompt = f"""
Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Current hour: {current_hour} (0-23)
Current day: {current_day} (0=Monday, 6=Sunday)

# Schedule-based logic
if current_hour == 2:  # 2 AM
    # Run heavy maintenance tasks
elif current_hour in [9, 17]:  # 9 AM, 5 PM
    # Send business hour notifications
elif current_day == 0 and current_hour == 8:  # Monday 8 AM
    # Weekly reports
"""
```

### Security Considerations

#### Limited Tool Access

```python
# Super agent should only have necessary tools
# Don't grant access to:
# - User data modification tools
# - Authentication tools
# - Critical system configuration tools

# Safe tools for super agent:
safe_tools = [
    BaseTools.tool_noop,
    tool_send_notification,
    tool_generate_reports,
    tool_cleanup_temp_data,
]
```

#### Rate Limiting and Resource Management

```python
# Implement safeguards
MAX_TOOLS_PER_RUN = 5
MAX_EXECUTION_TIME = 300  # 5 minutes
MAX_API_CALLS_PER_HOUR = 100

# Monitor resource usage
if execution_time > MAX_EXECUTION_TIME:
    logger.warning("Super agent execution timeout")
    return None
```

### Future Expansion Possibilities

#### 1. AI-Driven Optimization

- Automatic parameter tuning based on performance
- Predictive maintenance scheduling
- Dynamic resource allocation

#### 2. Multi-Agent Coordination

- Agent-to-agent communication
- Distributed task processing
- Load balancing across instances

#### 3. External Integration

- Integration with external monitoring systems
- API-driven task scheduling
- Event-driven super agent triggers

#### 4. Advanced Analytics

- Performance trend analysis
- Predictive failure detection
- Automated decision optimization

### Monitoring and Debugging

#### Logging Strategy

```python
# Comprehensive logging in super agent
self.logger.info(f"Super agent starting: {datetime.now()}")
self.logger.debug(f"Available tools: {[t.__name__ for t in tools]}")
self.logger.info(f"Super agent completed successfully")
self.logger.error(f"Super agent failed: {error}")
```

#### Metrics Collection

- Execution frequency and duration
- Tool usage patterns
- Success/failure rates
- Resource consumption
- Output quality assessment

## Future Considerations

### Model Updates

- Monitor new model releases on OpenRouter
- Evaluate cost/performance ratios quarterly
- Consider specialized models for specific use cases

### Scaling Considerations

- Implement model load balancing for high volume
- Consider dedicated model instances for critical applications
- Monitor token usage patterns for optimization

### Alternative Providers

- Keep OPENAI_API_KEY and MISTRAL_API_KEY for potential direct integration
- Evaluate provider-specific features vs. OpenRouter convenience
- Consider hybrid approach for different use cases
