# Gemini 2.5 Integration Strategy for EasyLog Agent

## Overview

The EasyLog Agent is heavily dependent on function calling for Multiple Choice, Questionnaires, Charts, Notifications, and other tools. Since Gemini 2.5 has limited function calling support, we need a strategic approach to enable its use while maintaining full functionality.

## Current Tool Dependencies in EasyLog Agent

The agent uses these critical function-calling tools:

- `tool_ask_multiple_choice` - Essential for questionnaires
- `tool_answer_questionaire_question` / `tool_get_questionaire_answer` - Core functionality
- `tool_create_zlm_chart` / `tool_create_bar_chart` / `tool_create_line_chart` - Visualizations
- `tool_send_notification` - Push notifications
- `tool_search_documents` / `tool_get_document_contents` - Knowledge base
- Multiple EasyLog backend and SQL tools
- Memory, reminders, and scheduling tools

## Recommended Solution: Hybrid Model Architecture

### Strategy: Automatic Model Fallback for Tool Operations

```python
# Add to EasyLogAgent class
async def get_effective_model_for_operation(self, role_config: RoleConfig, needs_tools: bool) -> str:
    """
    Determine the best model to use based on operation requirements.

    For Gemini models, fallback to Claude for tool-heavy operations,
    but allow Gemini for conversational responses.
    """
    requested_model = role_config.model

    # Gemini models - limited function calling
    if "gemini" in requested_model.lower():
        if needs_tools:
            # Fallback to compatible model for tool operations
            fallback_model = "anthropic/claude-3.5-sonnet"
            self.logger.info(f"Using {fallback_model} for tool operation (requested: {requested_model})")
            return fallback_model
        else:
            # Use Gemini for pure conversational responses
            return requested_model

    return requested_model

def requires_function_calling(self, tools_values: list) -> bool:
    """Check if the current operation requires function calling."""
    function_calling_tools = {
        "tool_ask_multiple_choice",
        "tool_answer_questionaire_question",
        "tool_get_questionaire_answer",
        "tool_create_zlm_chart",
        "tool_create_bar_chart",
        "tool_create_line_chart",
        "tool_send_notification",
        "tool_search_documents",
        "tool_get_document_contents"
    }

    return any(tool.__name__ in function_calling_tools for tool in tools_values)
```

### Updated `on_message` Method

```python
async def on_message(
    self, messages: Iterable[ChatCompletionMessageParam]
) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
    # Get the current role
    role_config = await self.get_current_role()

    # Get the available tools
    tools = self.get_tools()

    # Filter tools based on the role's regex pattern
    tools_values = [
        tool
        for tool in tools.values()
        if re.match(role_config.tools_regex, tool.__name__)
        or tool.__name__ == BaseTools.tool_noop.__name__
        or tool.__name__ == BaseTools.tool_call_super_agent.__name__
    ]

    # Determine if we need function calling
    needs_tools = self.requires_function_calling(tools_values)

    # Get effective model (with potential fallback)
    effective_model = await self.get_effective_model_for_operation(role_config, needs_tools)

    # [Rest of the method remains the same until the completion call]

    # Create the completion request with effective model
    response = await self.client.chat.completions.create(
        model=effective_model,  # Use effective model instead of role_config.model
        messages=[
            {
                "role": "system",
                "content": llm_content,
            },
            *messages,
        ],
        stream=True,
        tools=[function_to_openai_tool(tool) for tool in tools_values] if needs_tools else None,
        tool_choice="auto" if needs_tools else None,
    )

    return response, list(tools_values)
```

## Alternative Solution: Gemini-Specific Schema Conversion

If you want to use Gemini 2.5 for tool operations, implement Google's function calling format:

```python
def convert_tools_for_gemini(self, openai_tools: list) -> list:
    """Convert OpenAI tool format to Google's Gemini format."""
    gemini_tools = []

    for tool_spec in openai_tools:
        if tool_spec.get('type') == 'function':
            func = tool_spec['function']
            gemini_tool = {
                'name': func['name'],
                'description': func['description'],
                'parameters': {
                    'type': 'object',
                    'properties': func['parameters']['properties'],
                    'required': func['parameters'].get('required', [])
                }
            }
            gemini_tools.append(gemini_tool)

    return gemini_tools

async def call_gemini_with_tools(self, model: str, messages: list, tools: list) -> Any:
    """Special handler for Gemini models with tool calling."""
    gemini_tools = self.convert_tools_for_gemini(
        [function_to_openai_tool(tool) for tool in tools]
    )

    response = await self.client.chat.completions.create(
        model=model,
        messages=messages,
        tools=gemini_tools,
        tool_choice="auto",
        # Gemini-specific parameters
        extra_body={
            "generationConfig": {
                "temperature": 0.1,
                "candidateCount": 1
            }
        }
    )

    return response
```

## Configuration Approach

### Option 1: Role-Level Fallback Configuration

```python
class RoleConfig(BaseModel):
    # Existing fields...
    model: str = Field(default="anthropic/claude-sonnet-4")

    # New field for fallback strategy
    tool_fallback_model: str | None = Field(
        default=None,
        description="Model to use for tool operations if primary model has limited function calling support"
    )

    # Usage example:
    # {
    #     "name": "GeminiRole",
    #     "model": "google/gemini-2.5-flash-preview",
    #     "tool_fallback_model": "anthropic/claude-3.5-sonnet",
    #     "prompt": "You are a helpful assistant using Gemini..."
    # }
```

### Option 2: Smart Model Detection

```python
# Add to agent configuration
GEMINI_MODELS = [
    "google/gemini-2.5-flash-preview",
    "google/gemini-2.5-pro-preview",
    "google/gemini-1.5-flash",
    "google/gemini-1.5-pro"
]

TOOL_COMPATIBLE_FALLBACK = "anthropic/claude-3.5-sonnet"

def is_gemini_model(self, model: str) -> bool:
    return any(gemini in model.lower() for gemini in ["gemini", "google/"])
```

## User Experience Strategy

### Transparent Model Switching

```python
async def log_model_usage(self, requested_model: str, actual_model: str, reason: str):
    """Log model usage for transparency."""
    if requested_model != actual_model:
        self.logger.info(f"Model fallback: {requested_model} -> {actual_model} ({reason})")

        # Optionally store in metadata for user visibility
        usage_log = await self.get_metadata("model_usage_log", [])
        usage_log.append({
            "timestamp": datetime.now().isoformat(),
            "requested": requested_model,
            "actual": actual_model,
            "reason": reason
        })
        await self.set_metadata("model_usage_log", usage_log[-10:])  # Keep last 10 entries
```

## Implementation Priority

### Phase 1: Basic Fallback (Recommended for now)

1. Implement automatic fallback to Claude 3.5 for tool operations
2. Allow Gemini for conversational responses without tools
3. Add logging for transparency

### Phase 2: Advanced Integration (Future)

1. Implement Gemini-specific schema conversion
2. Add role-level fallback configuration
3. Create hybrid conversation flows

### Phase 3: Optimization (Later)

1. Intelligent tool operation detection
2. Conversation context preservation across model switches
3. Performance optimization

## Example Role Configuration

```python
# Gemini role with automatic fallback
{
    "name": "GeminiAssistant",
    "prompt": "Je bent een vriendelijke assistent die gebruikt maakt van Gemini's krachtige mogelijkheden voor conversatie en analyse.",
    "model": "google/gemini-2.5-flash-preview",
    "tools_regex": ".*",  # Allow all tools (will auto-fallback for function calling)
    "allowed_subjects": None,
    "questionaire": []
}
```

## Benefits of This Approach

1. **Immediate Compatibility**: Works with current codebase
2. **Transparent Fallback**: Users can use Gemini models in role config
3. **Full Functionality**: All tools continue working via fallback
4. **Performance**: Gemini for conversation, Claude for tools
5. **Future-Proof**: Can add native Gemini tool support later
6. **User Choice**: Roles can specify different models

## Testing Strategy

```python
async def test_gemini_integration():
    """Test Gemini integration with tool fallback."""

    test_cases = [
        {
            "model": "google/gemini-2.5-flash-preview",
            "operation": "conversation",
            "should_use": "google/gemini-2.5-flash-preview"
        },
        {
            "model": "google/gemini-2.5-flash-preview",
            "operation": "multiple_choice",
            "should_use": "anthropic/claude-3.5-sonnet"
        },
        {
            "model": "anthropic/claude-3.5-sonnet",
            "operation": "multiple_choice",
            "should_use": "anthropic/claude-3.5-sonnet"
        }
    ]

    for test in test_cases:
        # Test logic here
        pass
```

This approach gives you the best of both worlds: Gemini's capabilities for conversation and Claude's reliability for tool operations!
