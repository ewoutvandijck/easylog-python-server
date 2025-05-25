# Agent Architecture Documentation

## Overview

This document provides comprehensive instructions for understanding and working with the agent system in the EasyLog Python server project. The system implements a modular agent architecture where different agents can be configured with specific roles, tools, and capabilities.

## Architecture Pattern

### Base Agent Structure

All agents inherit from `BaseAgent[TConfig]` located in `apps/api/src/agents/base_agent.py`. The base class provides:

- **Generic Configuration**: Type-safe configuration through `TConfig` parameter
- **Thread Management**: Persistent conversation threads with metadata storage
- **Tool Integration**: Standardized tool calling mechanism
- **Super Agent Support**: Background task processing capabilities
- **Document Search**: Weaviate-based semantic document search
- **Stream Handling**: Real-time message streaming

### Key Components

1. **Agent Classes**: Implement specific business logic and tool access
2. **Configuration Models**: Pydantic models defining agent behavior
3. **Tools**: Modular functions that agents can execute
4. **Super Agents**: Background agents for scheduled tasks
5. **Role System**: Multi-persona capability within single agent

## Available Agents

### 1. MUMCAgent (`agents/mumc_agent.py`)

**Purpose**: Medical University Medical Center assistant with health-focused capabilities

**Configuration**: `MUMCAgentConfig`

- Default role: "MUMCAssistant"
- Default model: "anthropic/claude-sonnet-4"
- Super agent interval: 3 hours (10800 seconds)

**Key Features**:

- ZLM (Ziektelastmeter COPD) chart creation with custom color schemes
- Medical data visualization tools
- Multi-language support (Dutch/English)
- Health-focused questionnaire system

**Unique Tools**:

```python
tool_create_zlm_chart()  # Medical burden meter charts
```

### 2. EasyLogAgent (`agents/easylog_agent.py`)

**Purpose**: General EasyLog platform assistant with business capabilities

**Configuration**: `EasyLogAgentConfig`

- Default role: "EasyLogAssistant"
- Default model: "anthropic/claude-sonnet-4"
- Super agent interval: 3 hours (10800 seconds)

**Key Features**:

- Business data visualization
- Planning and resource management integration
- SQL database access
- Backend API integration

### 3. DebugAgent (`agents/debug_agent.py`)

**Purpose**: Development and debugging assistant

**Configuration**: `DebugAgentConfig`

- Default role: "James"
- Default model: "openai/gpt-4.1"
- Super agent interval: 2 hours (7200 seconds)

**Key Features**:

- Simplified tool set for debugging
- Questionnaire testing capabilities
- Basic notification system

## Configuration System

### Role Configuration (`RoleConfig`)

Each agent supports multiple roles with individual configurations:

```python
class RoleConfig(BaseModel):
    name: str                                    # Role identifier
    prompt: str                                  # System prompt for the role
    model: str                                   # LLM model to use
    tools_regex: str                            # Tool access pattern (regex)
    allowed_subjects: list[str] | None          # Knowledge base restrictions
    questionnaire: list[QuestionaireQuestionConfig]  # Dynamic questions
```

### Questionnaire System

Dynamic question system for collecting user information:

```python
class QuestionaireQuestionConfig(BaseModel):
    question: str      # The question text
    instructions: str  # AI guidance for answering
    name: str         # Unique identifier for template substitution
```

**Template Usage**: `{questionnaire_{name}_answer}` in prompts

## Tool Architecture

### Tool Categories

#### 1. Core System Tools (`BaseTools`)

**Location**: `apps/api/src/agents/tools/base_tools.py`

**Purpose**: Fundamental system operations

**Tools**:

- `tool_noop()`: Explicit no-operation for controlled inaction
- `tool_call_super_agent()`: Trigger background processing

**Implementation**: Abstract base class requiring `all_tools()` method

#### 2. Role Management Tools

- `tool_set_current_role(role: str)`: Switch agent persona
- `tool_get_questionnaire_answer(question_name: str)`: Retrieve stored answers
- `tool_answer_questionnaire_question(question_name: str, answer: str)`: Store answers

#### 3. Knowledge Management Tools

**Document Search Integration**:

- `tool_search_documents(search_query: str)`: Semantic document search via Weaviate
- `tool_get_document_contents(path: str)`: Retrieve full document content from Prisma

**Knowledge Graph Tools** (`KnowledgeGraphTools`):

**Location**: `apps/api/src/agents/tools/knowledge_graph_tools.py`

**Service**: Graphiti connection for episodic memory

**Tools**:

```python
# Store conversation episodes for long-term memory
tool_store_episode(conversation_summary: str, episode_body: str) -> None

# Search knowledge base for relevant information
tool_search_knowledge_base(query: str) -> str
```

**Features**:

- Entity type support through Pydantic models
- Group-based knowledge isolation
- Episodic memory with temporal awareness
- Semantic search capabilities

#### 4. Visualization Tools

**Chart Widget System** (`ChartWidget`):

**Location**: `apps/api/src/models/chart_widget.py`

**Color Role System**:

```python
DEFAULT_COLOR_ROLE_MAP = {
    "success": "#b2f2bb",  # Pastel Green
    "neutral": "#a1c9f4",   # Pastel Blue
    "warning": "#ffb3ba",   # Pastel Red
    "info": "#FFFACD",      # LemonChiffon
    "primary": "#DDA0DD",   # Plum
    "accent": "#B0E0E6",    # PowderBlue
    "muted": "#D3D3D3",     # LightGray
}
```

**Chart Types**:

**Bar Charts**:

```python
ChartWidget.create_bar_chart(
    title: str,
    data: list[dict[str, Any]],  # Format: {"value": number, "colorRole": str}
    x_key: str,
    y_keys: list[str],
    y_labels: list[str] | None = None,
    custom_color_role_map: dict[str, str] | None = None,
    horizontal_lines: list[Line] | None = None,
    height: int = 400,
    y_axis_domain_min: float | None = None,
    y_axis_domain_max: float | None = None
) -> ChartWidget
```

**Line Charts**:

```python
ChartWidget.create_line_chart(
    title: str,
    data: list[dict[str, Any]],  # Direct numerical values
    x_key: str,
    y_keys: list[str],
    custom_series_colors_palette: list[str] | None = None,
    height: int = 400,
    y_axis_domain_min: float | None = None,
    y_axis_domain_max: float | None = None
) -> ChartWidget
```

**ZLM Charts** (MUMC only):

```python
tool_create_zlm_chart(
    language: Literal["nl", "en"],
    data: list[dict[str, Any]],  # 0-100 percentage values
    x_key: str,
    y_keys: list[str],
    height: int = 1000
) -> ChartWidget
```

**Advanced Chart Features**:

- `ChartDataRow`: Structured data with x-value and y-values mapping
- `ChartDataPointValue`: Individual point with value and color
- `Line`: Horizontal reference lines with labels
- `AxisConfig`: Comprehensive axis configuration
- `TooltipConfig`: Interactive tooltip customization
- `SeriesConfig`: Data series styling and behavior

#### 5. Interaction Tools

- `tool_ask_multiple_choice()`: Present choice widgets to users
- `tool_download_image(url: str)`: Process external images with automatic resizing and format conversion

#### 6. Scheduling Tools

- `tool_set_recurring_task(cron_expression: str, task: str)`: Schedule recurring tasks
- `tool_add_reminder(date: str, message: str)`: Create one-time reminders
- `tool_remove_recurring_task(id: str)`: Delete scheduled tasks
- `tool_remove_reminder(id: str)`: Delete reminders

#### 7. Memory Tools

- `tool_store_memory(memory: str)`: Persistent information storage
- `tool_get_memory(id: str)`: Retrieve stored information

#### 8. Notification Tools (`OneSignalService`)

**Location**: `apps/api/src/services/one_signal/one_signal_service.py`

**Configuration**:

```python
class OneSignalService:
    def __init__(self):
        self.configuration = onesignal.Configuration(
            app_key=settings.ONESIGNAL_API_KEY,
        )
```

**Tools**:

- `tool_send_notification(title: str, contents: str)`: Push notifications via OneSignal
- Support for external user IDs and custom data payloads
- Notification history tracking in agent metadata

#### 9. EasyLog-Specific Tools

**Backend Tools** (`EasylogBackendTools`):

**Location**: `apps/api/src/agents/tools/easylog_backend_tools.py`

**Service**: `EasylogBackendService` via HTTP API

**Configuration**:

```python
def __init__(
    self,
    bearer_token: str = "",
    base_url: str = "https://staging.easylog.nu/api/v2",
    max_tool_result_length: int = 3250,
) -> None:
```

**Project Management Tools**:

```python
# Project CRUD operations
tool_get_planning_projects(from_date: str | None, to_date: str | None) -> str
tool_get_planning_project(project_id: int) -> str
tool_update_planning_project(project_id: int, **kwargs) -> str

# Phase management
tool_get_planning_phases(project_id: int) -> str
tool_get_planning_phase(phase_id: int) -> str
tool_update_planning_phase(phase_id: int, start: str, end: str) -> str
tool_create_planning_phase(project_id: int, slug: str, start: str, end: str) -> str

# Resource management
tool_get_resources() -> str
tool_get_projects_of_resource(resource_group_id: int, slug: str) -> str
tool_get_resource_groups(resource_id: int, resource_group_slug: str) -> str

# Resource allocation
tool_create_multiple_allocations(project_id: int, group: str, resources: list) -> str
```

**API Endpoints**:

- `/datasources/projects` - Project listing and filtering
- `/datasources/projects/{id}` - Individual project CRUD
- `/datasources/project/{id}/phases` - Phase management
- `/datasources/resources` - Resource management
- `/datasources/resources/{id}/projects/{slug}` - Resource-project relationships

**SQL Tools** (`EasylogSqlTools`):

**Location**: `apps/api/src/agents/tools/easylog_sql_tools.py`

**Service**: `EasylogSqlService` with SSH tunnel support

**Configuration**:

```python
def __init__(
    self,
    ssh_key_path: str | None = None,
    ssh_host: str | None = None,
    ssh_username: str | None = None,
    db_host: str = "127.0.0.1",
    db_port: int = 3306,
    db_user: str = "easylog",
    db_name: str = "easylog",
    db_password: str = "",
    connect_timeout: int = 10,
) -> None:
```

**Database Access**:

```python
# Direct SQL query execution
tool_execute_query(query: str) -> str
```

**SSH Tunnel Features**:

- Automatic SSH tunnel creation when credentials provided
- PyMySQL connection management
- Context manager for connection safety
- Connection pooling and cleanup

**Security Features**:

- SSH key-based authentication
- Configurable connection timeouts
- Automatic connection cleanup
- Error handling and logging

## Super Agent System

### Purpose

Background agents that run on scheduled intervals to:

- Process reminders and recurring tasks
- Send notifications for due items
- Perform maintenance operations

### Configuration

```python
@staticmethod
def super_agent_config() -> SuperAgentConfig[TConfig] | None:
    return SuperAgentConfig(
        interval_seconds=10800,  # 3 hours
        agent_config=AgentConfig(),
    )
```

### Implementation Pattern

```python
async def on_super_agent_call(self, messages) -> tuple[...] | None:
    # 1. Gather current state (notifications, reminders, tasks)
    # 2. Evaluate what needs processing
    # 3. Execute actions (send notifications or noop)
    # 4. Return appropriate tool calls
```

## Data Models

### Chart Widgets

**Color Role System**:

- `"success"`: Green colors (positive metrics)
- `"warning"`: Red/orange colors (attention needed)
- `"neutral"`: Gray/blue colors (informational)
- `"info"`: Blue colors (general information)

**ZLM Color Mapping**:

- 0-40: `"warning"` (poor health metrics)
- 40-70: `"neutral"` (moderate health metrics)
- 70-100: `"success"` (good health metrics)

**Chart Data Structure**:

```python
class ChartDataRow(BaseModel):
    x_value: str
    y_values: dict[str, ChartDataPointValue]

class ChartDataPointValue(BaseModel):
    value: float | str
    color: str  # HEX color
```

### Multiple Choice Widgets

```python
MultipleChoiceWidget(
    question: str,
    choices: list[Choice],  # Choice(label: str, value: str)
    selected_choice: Choice | None
)
```

## Implementation Guidelines

### Adding New Agents

1. **Create Agent Class**:

```python
class NewAgent(BaseAgent[NewAgentConfig]):
    async def on_message(self, messages) -> tuple[...]:
        # Main message handling logic

    async def on_super_agent_call(self, messages) -> tuple[...]:
        # Background task logic

    def get_tools(self) -> dict[str, Callable]:
        # Tool registration

    @staticmethod
    def super_agent_config() -> SuperAgentConfig[NewAgentConfig]:
        # Background task configuration
```

2. **Define Configuration**:

```python
class NewAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(default_factory=lambda: [...])
    prompt: str = Field(default="...")
```

3. **Register Tools**: Include all relevant tool categories based on agent purpose

### Adding New Tools

1. **Function Definition**:

```python
async def tool_new_functionality(param1: str, param2: int) -> str:
    """Tool description for LLM understanding.

    Args:
        param1: Parameter description
        param2: Parameter description

    Returns:
        Description of return value
    """
    # Implementation
    return result
```

2. **Registration**: Add to agent's `get_tools()` method

3. **Documentation**: Update this file with tool description

### Creating New Tool Categories

1. **Inherit from BaseTools**:

```python
class NewToolCategory(BaseTools):
    def __init__(self, **config_params):
        # Initialize service connections

    @property
    def all_tools(self) -> list[Callable]:
        return [self.tool_method_1, self.tool_method_2]
```

2. **Implement Service Layer**: Create corresponding service class in `src/services/`

3. **Add to Agents**: Include in relevant agent `get_tools()` methods

### Best Practices

#### Tool Design

- **Clear docstrings**: LLM uses these for understanding
- **Type hints**: Enable proper validation
- **Error handling**: Graceful failure with informative messages
- **Async patterns**: Non-blocking operations
- **Result formatting**: JSON serialization for complex data

#### Service Integration

- **Connection management**: Use context managers for resource cleanup
- **Configuration**: Environment variables for sensitive data
- **Logging**: Comprehensive logging for debugging
- **Error propagation**: Meaningful error messages for LLM

#### Chart Implementation

- **Color consistency**: Use defined color role maps
- **Data validation**: Ensure proper data structure
- **Responsive design**: Configurable dimensions
- **Accessibility**: Consider color-blind users

#### Database Access

- **Connection security**: SSH tunnels for remote access
- **Query safety**: Parameterized queries to prevent injection
- **Connection pooling**: Efficient resource utilization
- **Timeout handling**: Prevent hanging connections

#### Security Considerations

- **Input validation**: Sanitize all user inputs
- **Tool access control**: Use `tools_regex` to limit capabilities
- **Subject restrictions**: Limit knowledge base access per role
- **Credential management**: Environment variables only
- **Connection encryption**: SSH tunnels and TLS

## Troubleshooting

### Common Issues

1. **Import Errors**:

   - Check OneSignal package installation: `pip install onesignal-sdk`
   - Verify path imports match project structure
   - Ensure all dependencies in requirements.txt

2. **Tool Not Found**:

   - Ensure tool is registered in `get_tools()`
   - Check `tools_regex` allows the tool name
   - Verify tool function signature matches expected pattern

3. **Configuration Errors**:

   - Validate Pydantic model structure
   - Check default factory functions
   - Ensure environment variables are set

4. **Database Connection Issues**:

   - Verify SSH key exists and has correct permissions
   - Check SSH host connectivity
   - Validate database credentials
   - Test connection timeout settings

5. **Chart Rendering Issues**:

   - Validate data structure matches expected format
   - Check color role mappings
   - Ensure y-axis domain settings are correct
   - Verify data type consistency

6. **Super Agent Not Running**:
   - Verify `super_agent_config()` returns valid configuration
   - Check interval timing and cron expressions
   - Validate notification system integration

### Debug Strategies

1. **Use DebugAgent**: Simplified tool set for testing
2. **Check Logs**: Agent initialization and tool execution logs
3. **Validate Data**: Use Pydantic validation for input checking
4. **Test Tools Individually**: Isolate tool functionality
5. **Service Testing**: Test underlying services directly
6. **Connection Testing**: Verify database and API connectivity

## Development Workflow

### Testing New Features

1. Implement in DebugAgent first
2. Test with simplified configuration
3. Move to target agent when stable
4. Update documentation

### Service Development

1. Create service class in `src/services/`
2. Implement tool wrapper in `src/agents/tools/`
3. Add comprehensive error handling
4. Write integration tests
5. Document API endpoints and parameters

### Code Reviews

- Verify tool docstrings are LLM-friendly
- Check configuration consistency across agents
- Ensure proper error handling
- Validate security considerations
- Review service integration patterns
- Check connection management

### Deployment

- Test super agent intervals in staging
- Verify notification system integration
- Check database connectivity (SQL tools)
- Validate external API integrations (EasyLog)
- Test SSH tunnel functionality
- Verify environment variable configuration

## Future Considerations

### Scalability

- Consider tool result caching for frequently used operations
- Implement tool result compression for large datasets
- Add tool execution time monitoring
- Connection pooling optimization
- API rate limiting and retry logic

### Enhanced Features

- Cross-agent communication capabilities
- Advanced scheduling with timezone support
- Enhanced security with role-based permissions
- Tool usage analytics and optimization
- Real-time collaboration tools
- Advanced chart types (scatter, radar, etc.)

### Integration Opportunities

- External API tool generators
- Dynamic tool loading from configuration
- AI-powered tool selection optimization
- Enhanced knowledge base integration
- Multi-database support
- Advanced visualization libraries
- Real-time data streaming capabilities

### Performance Optimization

- Tool execution caching
- Database connection pooling
- Chart rendering optimization
- Memory usage monitoring
- Async tool execution batching
- Result pagination for large datasets
