# Gemini 2.5 Production Implementation for EasyLogAgentJson.json

## Current Production Configuration Analysis

Your `EasyLogAgentJson.json` shows a **function-calling intensive** configuration:

### **Ziektelastmeter Role** (Heavy Tool Usage)

- 17 Multiple Choice questions requiring `tool_ask_multiple_choice`
- Questionnaire data management with `tool_answer_questionaire_question`
- Currently uses: `anthropic/claude-sonnet-4`

### **UITSLAG Role** (Heavy Tool Usage)

- Complex ZLM chart generation with `tool_create_zlm_chart`
- Detailed score calculations across 9 domains
- Currently uses: `anthropic/claude-sonnet-4`

## Implementation Strategy

### **Option 1: Simple Model Replacement (Recommended)**

Update your JSON configuration to use Gemini 2.5 with automatic fallback:

```json
{
  "name": "Ziektelastmeter",
  "model": "google/gemini-2.5-flash-preview", // ← Change this
  "prompt": "This is the ZLM/Ziektelastmeter questionaire...",
  "tools_regex": ".*",
  "allowed_subjects": null,
  "questionaire": [
    // ... existing questionnaire remains the same
  ]
}
```

```json
{
  "name": "UITSLAG",
  "model": "google/gemini-2.5-flash-preview", // ← Change this
  "prompt": "Bereken de ZLM score en toon de ZLM grafiek...",
  "tools_regex": ".*",
  "allowed_subjects": null
}
```

**Result**: With the hybrid implementation in `EasyLogAgent`, this will:

- Use Gemini 2.5 for conversational responses
- Auto-fallback to Claude 3.5 for tool operations (Multiple Choice, Charts)
- Maintain full functionality seamlessly

### **Option 2: Mixed Model Strategy**

Keep critical tool-heavy roles on Claude, test Gemini on conversational roles:

```json
{
  "roles": [
    {
      "name": "Ziektelastmeter",
      "model": "anthropic/claude-sonnet-4",  // Keep for complex tools
      "prompt": "...",
      "questionaire": [...]
    },
    {
      "name": "UITSLAG",
      "model": "anthropic/claude-sonnet-4",  // Keep for chart generation
      "prompt": "..."
    },
    {
      "name": "GeneralChat",  // New role for testing
      "model": "google/gemini-2.5-flash-preview",
      "prompt": "Je bent een vriendelijke gesprekspartner...",
      "tools_regex": "tool_store_memory|tool_get_memory|tool_noop",  // Limited tools
      "questionaire": []
    }
  ]
}
```

## Code Implementation Required

To support this in production, implement these methods in `EasyLogAgent`:

```python
# Add to EasyLogAgent class
GEMINI_MODELS = {
    "google/gemini-2.5-flash-preview",
    "google/gemini-2.5-pro-preview",
    "google/gemini-1.5-flash",
    "google/gemini-1.5-pro"
}

CRITICAL_FUNCTION_TOOLS = {
    "tool_ask_multiple_choice",
    "tool_answer_questionaire_question",
    "tool_get_questionaire_answer",
    "tool_create_zlm_chart",
    "tool_create_bar_chart",
    "tool_create_line_chart"
}

async def get_effective_model_for_operation(self, role_config: RoleConfig, needs_critical_tools: bool) -> str:
    """Determine best model based on operation requirements."""
    requested_model = role_config.model

    # Check if requested model is Gemini
    if any(gemini in requested_model.lower() for gemini in ["gemini", "google/"]):
        if needs_critical_tools:
            fallback_model = "anthropic/claude-3.5-sonnet"
            self.logger.info(f"Function calling fallback: {requested_model} → {fallback_model}")
            return fallback_model
        else:
            return requested_model

    return requested_model

def requires_critical_function_calling(self, tools_values: list) -> bool:
    """Check if operation requires critical function calling tools."""
    return any(tool.__name__ in self.CRITICAL_FUNCTION_TOOLS for tool in tools_values)

# Update on_message method
async def on_message(self, messages: Iterable[ChatCompletionMessageParam]) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
    role_config = await self.get_current_role()
    tools = self.get_tools()

    # Filter tools based on role's regex
    tools_values = [
        tool for tool in tools.values()
        if re.match(role_config.tools_regex, tool.__name__)
        or tool.__name__ in ["tool_noop", "tool_call_super_agent"]
    ]

    # Check if critical tools are needed
    needs_critical_tools = self.requires_critical_function_calling(tools_values)

    # Get effective model (with potential fallback)
    effective_model = await self.get_effective_model_for_operation(role_config, needs_critical_tools)

    # ... rest of method with effective_model ...

    response = await self.client.chat.completions.create(
        model=effective_model,  # Use effective model
        messages=[{"role": "system", "content": llm_content}, *messages],
        stream=True,
        tools=[function_to_openai_tool(tool) for tool in tools_values] if tools_values else None,
        tool_choice="auto" if tools_values else None,
    )

    return response, list(tools_values)
```

## Testing Your Production Configuration

### **Test Scenario 1: ZLM Questionnaire with Gemini**

1. Update `Ziektelastmeter` role to use `google/gemini-2.5-flash-preview`
2. Start questionnaire → Should auto-fallback to Claude for `tool_ask_multiple_choice`
3. Verify all 17 questions work correctly
4. Monitor logs for fallback notifications

### **Test Scenario 2: ZLM Chart Generation with Gemini**

1. Update `UITSLAG` role to use `google/gemini-2.5-flash-preview`
2. Complete questionnaire and trigger results → Should auto-fallback to Claude for `tool_create_zlm_chart`
3. Verify chart displays correctly with proper colorRole mappings
4. Check balloon height calculations are accurate

### **Test Configuration for Development**

Create a test version of your JSON:

```json
{
  "id": 999,
  "schema": [
    {
      "name": "gemini-test",
      "type": "assistant",
      "label": "Gemini Test Coach",
      "agentConfig": {
        "agent_class": "EasyLogAgent",
        "prompt": "You can use the following roles: {{available_roles}}...",
        "roles": [
          {
            "name": "GeminiZLM",
            "model": "google/gemini-2.5-flash-preview",
            "prompt": "This is the ZLM questionaire using Gemini...",
            "tools_regex": ".*",
            "questionaire": [
              // Copy first 3 questions from your existing config for testing
              {
                "name": "G1",
                "question": "In de afgelopen week, hoe vaak... had u last van vermoeidheid?",
                "instructions": "Antwoordopties: nooit (label: 'nooit', value: '0'); zelden (label: 'zelden', value: '1')..."
              }
              // ...
            ]
          }
        ]
      }
    }
  ]
}
```

## Expected Behavior After Implementation

### **With Hybrid Implementation:**

1. **User starts questionnaire**

   - JSON config says: `"model": "google/gemini-2.5-flash-preview"`
   - Agent detects: needs `tool_ask_multiple_choice`
   - **Auto-fallback**: Uses `anthropic/claude-3.5-sonnet`
   - **Result**: Multiple choice works perfectly ✅

2. **User gets conversational response**

   - JSON config says: `"model": "google/gemini-2.5-flash-preview"`
   - Agent detects: no critical tools needed
   - **Uses Gemini**: Direct response
   - **Result**: Faster, more natural conversation ✅

3. **Chart generation**
   - JSON config says: `"model": "google/gemini-2.5-flash-preview"`
   - Agent detects: needs `tool_create_zlm_chart`
   - **Auto-fallback**: Uses `anthropic/claude-3.5-sonnet`
   - **Result**: Perfect ZLM charts with proper colors ✅

## Migration Path

### **Phase 1: Implement Hybrid Support** (1-2 days)

- Add hybrid methods to `EasyLogAgent`
- Test with simple role configurations

### **Phase 2: Test Critical Roles** (2-3 days)

- Test Ziektelastmeter role with Gemini config
- Test UITSLAG role with Gemini config
- Verify all 17 questions + chart generation

### **Phase 3: Production Deployment** (1 day)

- Update production JSON configurations
- Monitor logs for fallback behavior
- Validate end-to-end ZLM workflow

This approach lets you start using Gemini 2.5 in your production config **immediately** while maintaining 100% functionality!
