# Function Calling Compatibility Solutions for OpenRouter Models

## Overview

The Multiple Choice, Questionnaire, and Noop tools are failing with certain OpenRouter models due to fundamental differences in function calling support and implementation. This document provides detailed solutions.

## Root Cause Analysis

### Model-Specific Function Calling Support Matrix

| Model                             | Function Calling Support | Status        | Notes                        |
| --------------------------------- | ------------------------ | ------------- | ---------------------------- |
| `anthropic/claude-3.7-sonnet`     | ❌ **NO**                | Not Supported | Uses structured prompts only |
| `google/gemini-2.5-flash-preview` | ⚠️ **LIMITED**           | Partial       | Different JSON schema format |
| `anthropic/claude-3.5-sonnet`     | ✅ **YES**               | Full Support  | Works correctly              |
| `openai/gpt-4.1`                  | ✅ **YES**               | Full Support  | Reference implementation     |
| `anthropic/claude-3-sonnet`       | ✅ **YES**               | Full Support  | Works correctly              |

### Technical Issues Identified

1. **Claude 3.7 Sonnet**: Completely lacks function calling capability
2. **Gemini 2.5 Models**: Use Google-specific function calling schema
3. **OpenRouter Normalization**: Incomplete standardization across providers

## Solution 1: Model Filtering by Function Calling Capability

### Update Agent Configuration

Add function calling capability checks to your agent selection logic:

```python
# In agents/base_agent.py or configuration
FUNCTION_CALLING_SUPPORTED_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-sonnet",
    "openai/gpt-4.1",
    "openai/gpt-4",
    "openai/gpt-3.5-turbo",
    # Add other confirmed working models
]

FUNCTION_CALLING_LIMITED_MODELS = [
    "google/gemini-2.5-flash-preview",
    "google/gemini-2.5-pro-preview",
    # These need special handling
]

FUNCTION_CALLING_UNSUPPORTED_MODELS = [
    "anthropic/claude-3.7-sonnet",
    # These cannot use tools at all
]
```

### Implementation in Agent

```python
async def select_model_for_tools(self, requested_model: str, needs_tools: bool) -> str:
    """Select appropriate model based on tool requirements."""

    if not needs_tools:
        return requested_model  # Any model works for non-tool tasks

    if requested_model in FUNCTION_CALLING_UNSUPPORTED_MODELS:
        # Fallback to supported model
        fallback_model = "anthropic/claude-3.5-sonnet"
        self.logger.warning(f"Model {requested_model} doesn't support function calling. Using {fallback_model}")
        return fallback_model

    if requested_model in FUNCTION_CALLING_LIMITED_MODELS:
        # Use Google-specific handling
        return self.handle_google_function_calling(requested_model)

    return requested_model

def uses_tools(self, tools_list: list) -> bool:
    """Check if any of the requested tools require function calling."""
    tool_calling_tools = [
        "tool_ask_multiple_choice",
        "tool_answer_questionnaire_question",
        "tool_get_questionnaire_answer",
        "tool_noop"
    ]

    for tool in tools_list:
        if hasattr(tool, '__name__') and tool.__name__ in tool_calling_tools:
            return True
    return False
```

## Solution 2: Alternative Implementation for Non-Function-Calling Models

### Prompt-Based Multiple Choice for Claude 3.7

Since Claude 3.7 Sonnet excels at structured prompts, implement tools using prompt engineering:

```python
async def tool_ask_multiple_choice_prompt_based(self, question: str, choices: list) -> str:
    """Alternative implementation for models without function calling."""

    choices_text = "\n".join([f"{i+1}. {choice['label']}" for i, choice in enumerate(choices)])

    prompt = f"""
    Please answer this multiple choice question:

    {question}

    Options:
    {choices_text}

    Please respond with EXACTLY the number of your choice (1, 2, 3, etc.) followed by a colon and the choice text.
    Format: "X: [choice text]"
    """

    response = await self.generate_response(prompt)

    # Parse response to extract choice
    try:
        choice_num = int(response.strip().split(':')[0]) - 1
        if 0 <= choice_num < len(choices):
            return choices[choice_num]['value']
    except:
        pass

    # Fallback - return first choice
    return choices[0]['value'] if choices else ""

async def detect_model_capabilities(self, model_name: str) -> dict:
    """Detect what capabilities a model supports."""
    capabilities = {
        'function_calling': True,
        'structured_output': True,
        'reasoning_mode': False
    }

    # Claude 3.7 specific
    if 'claude-3.7' in model_name:
        capabilities.update({
            'function_calling': False,
            'structured_output': True,
            'reasoning_mode': True
        })

    # Gemini specific
    if 'gemini' in model_name:
        capabilities.update({
            'function_calling': 'limited',
            'requires_google_schema': True
        })

    return capabilities
```

## Solution 3: Google-Specific Function Calling Implementation

### Gemini Models Require Different Schema

```python
def convert_to_google_function_schema(self, openai_tools: list) -> list:
    """Convert OpenAI function schema to Google's format."""
    google_tools = []

    for tool in openai_tools:
        if tool.get('type') == 'function':
            func = tool['function']
            google_tool = {
                'name': func['name'],
                'description': func['description'],
                'parameters': {
                    'type': 'object',
                    'properties': func['parameters']['properties'],
                    'required': func['parameters'].get('required', [])
                }
            }
            google_tools.append(google_tool)

    return google_tools

async def call_gemini_with_tools(self, messages: list, tools: list) -> dict:
    """Special handling for Gemini models."""
    google_tools = self.convert_to_google_function_schema(tools)

    # Use Google-specific parameters
    response = await self.client.chat.completions.create(
        model=self.model_name,
        messages=messages,
        tools=google_tools,
        tool_choice="auto",  # Google prefers "auto" over "any"
        # Add Google-specific parameters
        extra_body={
            "generationConfig": {
                "temperature": 0.1,
                "candidateCount": 1
            }
        }
    )

    return response
```

## Solution 4: Graceful Degradation Strategy

### Implement Smart Fallbacks

```python
class ToolExecutionStrategy:

    async def execute_questionnaire_flow(self, model_capabilities: dict):
        """Execute questionnaire with appropriate strategy based on model."""

        if model_capabilities['function_calling'] is True:
            # Use standard function calling
            return await self.standard_function_calling_flow()

        elif model_capabilities.get('reasoning_mode'):
            # Use Claude 3.7's hybrid reasoning
            return await self.reasoning_mode_questionnaire()

        elif model_capabilities['function_calling'] == 'limited':
            # Use Google-specific implementation
            return await self.google_function_calling_flow()

        else:
            # Fallback to prompt-based
            return await self.prompt_based_questionnaire()

    async def reasoning_mode_questionnaire(self):
        """Use Claude 3.7's extended thinking for questionnaires."""

        prompt = """
        Using your extended thinking capability, please work through this questionnaire step by step.

        Think through each question carefully, then provide structured responses.

        [questionnaire content here]

        Please think through this systematically and provide your responses in a structured format.
        """

        # Use Claude 3.7's thinking parameter
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            extra_body={
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 4000
                }
            }
        )

        return response
```

## Solution 5: Update OpenRouter Configuration

### Check OpenRouter Model Support

Use OpenRouter's model filtering to verify function calling support:

```python
async def get_supported_models_for_tools():
    """Get models that support function calling from OpenRouter."""

    # Query OpenRouter's models endpoint
    url = "https://openrouter.ai/api/v1/models"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            models_data = await response.json()

    # Filter models that support tools parameter
    supported_models = []
    for model in models_data.get('data', []):
        if 'tools' in model.get('supported_parameters', []):
            supported_models.append(model['id'])

    return supported_models
```

## Solution 6: Implementation Recommendations

### Priority Order for Implementation

1. **Immediate**: Update model selection to avoid Claude 3.7 for tool-based tasks
2. **Short-term**: Implement Google-specific function calling for Gemini models
3. **Medium-term**: Add prompt-based fallbacks for unsupported models
4. **Long-term**: Create unified tool execution layer that abstracts model differences

### Code Changes Required

1. **Update `lib/openai.py`**: Add model capability detection
2. **Update `agents/base_agent.py`**: Add tool compatibility checking
3. **Update agent configurations**: Specify tool-compatible models
4. **Create fallback implementations**: For unsupported models

### Testing Strategy

```python
async def test_tool_compatibility():
    """Test tool compatibility across models."""

    test_models = [
        "anthropic/claude-3.5-sonnet",  # Should work
        "anthropic/claude-3.7-sonnet",  # Should fallback
        "google/gemini-2.5-flash-preview",  # Should use Google schema
        "openai/gpt-4.1"  # Should work
    ]

    for model in test_models:
        try:
            result = await test_multiple_choice_tool(model)
            print(f"✅ {model}: {result}")
        except Exception as e:
            print(f"❌ {model}: {e}")
```

## Conclusion

The core issue is that **Claude 3.7 Sonnet fundamentally lacks function calling support**, while **Gemini models use different schemas**. The solution is to:

1. **Detect model capabilities** before selecting tools
2. **Use fallback models** for tool-dependent tasks
3. **Implement alternative strategies** for unsupported models
4. **Create Google-specific implementations** for Gemini models

This approach maintains compatibility across all OpenRouter models while leveraging each model's strengths appropriately.
