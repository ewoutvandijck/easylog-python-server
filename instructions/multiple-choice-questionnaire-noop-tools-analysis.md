# Multiple Choice, Questionnaire & Noop Tools - Comprehensive Analysis

## Overview

This document provides a detailed analysis of three critical tools in the EasyLog Python server system: Multiple Choice widgets, Questionnaire systems, and the Noop tool. These tools work together to create interactive user experiences and control agent behavior.

## 1. Multiple Choice Widget System

### Architecture Overview

The Multiple Choice system consists of several interconnected components:

**Backend Models** (`apps/api/src/models/multiple_choice_widget.py`):

```python
class Choice(BaseModel):
    label: str  # Display text shown to user
    value: str  # Internal value for processing

class MultipleChoiceWidget(BaseModel):
    type: Literal["multiple_choice"] = "multiple_choice"
    question: str                    # Question text
    choices: list[Choice]           # Available options
    selected_choice: str | None     # User's selection
```

**Frontend Integration** (`apps/web/src/schemas/multipleChoice.ts`):

```typescript
export const choiceSchema = z.object({
  label: z.string(),
  value: z.string()
});

export const multipleChoiceSchema = z.object({
  type: z.literal('multiple_choice'),
  question: z.string(),
  choices: z.array(choiceSchema),
  selected_choice: z.string().nullable().optional()
});
```

### Implementation Pattern

Every agent implements the same `tool_ask_multiple_choice` function:

```python
def tool_ask_multiple_choice(question: str, choices: list[dict[str, str]]) -> MultipleChoiceWidget:
    """Asks the user a multiple-choice question with distinct labels and values.
    When using this tool, you must not repeat the same question or answers in text
    unless asked to do so by the user. This widget already presents the question
    and choices to the user.

    Args:
        question: The question to ask.
        choices: A list of choice dictionaries, each with a 'label' (display text)
                 and a 'value' (internal value). Example:
                 [{'label': 'Yes', 'value': '0'}, {'label': 'No', 'value': '1'}]

    Returns:
        A MultipleChoiceWidget object representing the question and the choices.

    Raises:
        ValueError: If a choice dictionary is missing 'label' or 'value'.
    """
    parsed_choices = []
    for choice_dict in choices:
        if "label" not in choice_dict or "value" not in choice_dict:
            raise ValueError("Each choice dictionary must contain 'label' and 'value' keys.")
        parsed_choices.append(Choice(label=choice_dict["label"], value=choice_dict["value"]))

    return MultipleChoiceWidget(
        question=question,
        choices=parsed_choices,
        selected_choice=None,
    )
```

### Frontend Rendering

**React Component** (`apps/web/src/components/chat/ChatBubble.tsx`):

```tsx
content.widget_type === 'multiple_choice' ? (
  <div className="flex flex-col gap-2">
    {multipleChoiceSchema
      .parse(JSON.parse(content.output))
      .choices.map((choice) => (
        <button
          key={choice.value}
          className="rounded-lg px-4 py-2 bg-secondary"
          onClick={() => {
            sendMessage(threadId!, {
              agent_config: {
                agent_class: activeConfiguration?.agentConfig.agent_class ?? '',
                ...activeConfiguration?.agentConfig
              },
              content: [
                {
                  text: choice.value, // Sends the value, not the label
                  type: 'text'
                }
              ]
            });
          }}
        >
          {choice.label} {/* Displays the label */}
        </button>
      ))}
  </div>
) : null;
```

### Data Flow

1. **Agent calls `tool_ask_multiple_choice`** with question and choices
2. **BaseAgent processes** the MultipleChoiceWidget return value
3. **Widget serialized** as JSON in ToolResultContent with `widget_type="multiple_choice"`
4. **Frontend receives** the widget data and renders interactive buttons
5. **User clicks** a button, sending the `choice.value` back as a text message
6. **Agent receives** the value and can process the user's selection

### Current Usage Patterns

**Simple Yes/No Questions**:

```python
choices = [
    {'label': 'Ja', 'value': 'ja'},
    {'label': 'Nee', 'value': 'nee'}
]
```

**Likert Scale Questions** (ZLM Questionnaire):

```python
choices = [
    {'label': 'nooit', 'value': '0'},
    {'label': 'zelden', 'value': '1'},
    {'label': 'af en toe', 'value': '2'},
    {'label': 'regelmatig', 'value': '3'},
    {'label': 'heel vaak', 'value': '4'},
    {'label': 'meestal', 'value': '5'},
    {'label': 'altijd', 'value': '6'}
]
```

## 2. Questionnaire System

### Configuration Architecture

Questionnaires are defined in agent role configurations:

```python
class QuestionaireQuestionConfig(BaseModel):
    question: str = Field(
        description="The text of the question to present to the user."
    )
    instructions: str = Field(
        description="Additional guidance for the AI agent on how to answer the question."
    )
    name: str = Field(
        description="A unique identifier for this question, used for referencing the answer."
    )
```

### Template System

Questionnaire data is injected into prompts using double-curly-brace syntax:

```python
# Template variables available in prompts:
questionnaire_format_kwargs = {
    f"questionaire_{q_item.name}_question": q_item.question,
    f"questionaire_{q_item.name}_instructions": q_item.instructions,
    f"questionaire_{q_item.name}_name": q_item.name,
    f"questionaire_{q_item.name}_answer": await self.get_metadata(q_item.name, "[not answered]")
}
```

**Example Usage in Prompts**:

```
Ask the questions in the following order:
1. G1: {{questionaire_G1_question}} (Options: {{questionaire_G1_instructions}})
2. G2: {{questionaire_G2_question}} (Options: {{questionaire_G2_instructions}})
...

Your current ZLM G1 answer is: {{questionaire_G1_answer}}
```

### Persistence Tools

**Saving Answers**:

```python
async def tool_answer_questionaire_question(question_name: str, answer: str) -> str:
    """Answer a question from the questionaire.

    Args:
        question_name (str): The name of the question to answer.
        answer (str): The answer to the question.
    """
    await self.set_metadata(question_name, answer)
    return f"Answer to {question_name} set to {answer}"
```

**Retrieving Answers**:

```python
async def tool_get_questionaire_answer(question_name: str) -> str:
    """Get the answer to a question from the questionaire.

    Args:
        question_name (str): The name of the question to get the answer to.

    Returns:
        str: The answer to the question.
    """
    return await self.get_metadata(question_name, "[not answered]")
```

### Real-World Implementation: ZLM (Ziektelastmeter)

The ZLM questionnaire is a comprehensive medical assessment with 17 questions:

**General Questions (G1-G11)**:

- G1: Fatigue frequency
- G2: Sleep quality
- G3: Emotional distress
- G4: Medication burden
- G5-G7: Physical limitations (heavy, moderate, daily activities)
- G8: Work/social limitations
- G9: Relationship impact
- G10: Intimacy/sexuality issues
- G11: Future concerns

**COPD-Specific Questions (C1-C6)**:

- C1: Shortness of breath at rest
- C2: Shortness of breath during activity
- C3: Anxiety about breathlessness
- C4: Coughing frequency
- C5: Sputum production
- C6: Medication courses (0-4 scale)

### Workflow Pattern

The ZLM implementation demonstrates the standard questionnaire workflow:

```
1. Call tool_ask_multiple_choice with question and options
2. Call tool_noop to wait for user response
3. Save answer with tool_answer_questionaire_question
4. IMMEDIATELY proceed to next question
```

**Critical Implementation Note**:

```
"NEVER repeat a question that has already been answered. When you complete question G6,
you MUST move directly to G7. Never return to G6 after it has been answered."
```

### Data Processing & Visualization

After questionnaire completion, the system:

1. **Calculates domain scores** using complex algorithms
2. **Determines color classifications** (Green/Orange/Red)
3. **Generates ZLM chart** with balloon heights representing health status
4. **Provides interpretative text** for each domain

**Example Domain Calculation (Fatigue)**:

```
if G1 == 0: Color Green, Height 100%, "No fatigue complaints"
if G1 == 1: Color Orange, Height 80%, "Rare fatigue complaints"
if G1 == 2: Color Orange, Height 60%, "Occasional fatigue complaints"
if G1 > 2: Color Red, Height 40-0%, "Fatigue complaints"
```

## 3. Noop Tool System

### Core Implementation

**BaseTools.tool_noop** (`apps/api/src/agents/tools/base_tools.py`):

```python
@classmethod
def tool_noop(cls) -> None:
    """You can use this tool to explicitly do nothing. This is useful when you
    got the instruction to not do anything."""
    return None
```

### Strategic Usage Patterns

#### 1. Questionnaire Flow Control

**Primary Use Case**: Wait for user responses after multiple choice questions

```python
# Workflow in ZLM Agent prompt:
"For each question, you MUST follow this EXACT process:
1. Call the tool tool_ask_multiple_choice directly
2. Always wait for the user's answer by directly calling tool_noop
3. When you receive the user's answer, save it using tool_answer_questionaire_question"
```

**Why This Pattern Works**:

- `tool_ask_multiple_choice` sends widget to user
- `tool_noop` prevents agent from continuing immediately
- User's response triggers new agent execution with their answer
- Agent can then save the answer and proceed

#### 2. Super Agent Termination

**Background Process Control**:

```python
# In SuperAgentService.call_agent():
for message in generated_messages:
    for content in message.content:
        if isinstance(content, ToolUseContent) and content.name == BaseTools.tool_noop.__name__:
            return  # Stop execution
```

**Use Case**: Super agents use `tool_noop` to indicate "no action needed"

```python
# Notification management super agent decision logic:
"""
## Required Action
After analysis, you must take exactly ONE of these actions:
- If any eligible notifications are found: invoke the send_notification tool
- If no eligible notifications exist: invoke the noop tool
"""
```

#### 3. Conversation State Management

**Explicit Inaction**: When an agent needs to explicitly do nothing but communicate that decision:

```python
# Agent decides not to take action but wants to signal this decision
if no_action_required:
    return BaseTools.tool_noop()
```

### Technical Integration

**Tool Registration**: Every agent includes `tool_noop` in their tool registry:

```python
# In agent get_tools() method:
tools_list = [
    # ... other tools ...
    BaseTools.tool_noop,
    BaseTools.tool_call_super_agent,
]
```

**Filtering Compatibility**: Always passes tool filtering since it's essential:

```python
# In on_message():
tools_values = [
    tool for tool in tools.values()
    if re.match(role_config.tools_regex, tool.__name__)
    or tool.__name__ == BaseTools.tool_noop.__name__  # Always included
    or tool.__name__ == BaseTools.tool_call_super_agent.__name__
]
```

## Integration Patterns & Best Practices

### 1. Interactive Questionnaire Pattern

**Complete Implementation**:

```python
# Step 1: Present question
widget = tool_ask_multiple_choice(
    question="How often did you experience fatigue this week?",
    choices=[
        {'label': 'Never', 'value': '0'},
        {'label': 'Rarely', 'value': '1'},
        {'label': 'Sometimes', 'value': '2'},
        # ...
    ]
)

# Step 2: Wait for response
tool_noop()

# Step 3: Process user's response (in next execution)
# User's choice.value is received as text message
await tool_answer_questionaire_question("fatigue_frequency", user_response)

# Step 4: Continue to next question
# (Repeat pattern)
```

### 2. Conditional Logic with Saved Answers

**Smart Questionnaire Flow**:

```python
# Check existing answers before asking
previous_answer = await tool_get_questionaire_answer("consent_given")
if previous_answer == "yes":
    # Skip consent questions, go to main questionnaire
    pass
else:
    # Ask consent questions first
    pass
```

### 3. Data-Driven Visualizations

**Post-Questionnaire Processing**:

```python
# Collect all answers
answers = {}
for question_name in ["G1", "G2", "G3", ...]:
    answers[question_name] = await tool_get_questionaire_answer(question_name)

# Calculate domain scores
domain_scores = calculate_zlm_scores(answers)

# Generate visualization
chart_widget = tool_create_zlm_chart(
    data=domain_scores,
    title="Disease Burden Assessment",
    language="nl"
)
```

## Areas for Improvement

### 1. Multiple Choice Enhancements

**Current Limitations**:

- No support for multi-select options
- Limited styling/branding customization
- No conditional choice visibility
- Static choice lists only

**Improvement Opportunities**:

```python
class MultipleChoiceWidget(BaseModel):
    # Existing fields...
    multi_select: bool = False          # Allow multiple selections
    max_selections: int | None = None   # Limit selections
    conditional_logic: dict | None = None  # Dynamic choice visibility
    styling: dict | None = None         # Custom appearance
```

### 2. Questionnaire System Improvements

**Enhanced Configuration**:

```python
class QuestionaireQuestionConfig(BaseModel):
    # Existing fields...
    dependencies: list[str] = []        # Questions that must be answered first
    validation_rules: dict | None = None # Answer validation
    skip_conditions: dict | None = None  # When to skip this question
    presentation_type: str = "multiple_choice"  # Support other input types
```

**Progress Tracking**:

```python
async def tool_get_questionnaire_progress() -> dict:
    """Return completion status and progress percentage."""
    pass

async def tool_validate_questionnaire_completion() -> bool:
    """Check if all required questions are answered."""
    pass
```

### 3. Noop Tool Extensions

**Enhanced Control Flow**:

```python
@classmethod
def tool_noop_with_reason(cls, reason: str) -> None:
    """Explicit no-op with reasoning for better debugging."""
    return None

@classmethod
def tool_wait_for_user_input(cls, timeout_seconds: int = 300) -> None:
    """Wait for user input with timeout."""
    return None
```

### 4. Error Handling & Recovery

**Robust Error Management**:

```python
async def tool_reset_questionnaire_progress(questionnaire_name: str) -> str:
    """Reset questionnaire if user wants to start over."""
    pass

async def tool_validate_questionnaire_answer(question_name: str, answer: str) -> bool:
    """Validate answer format before saving."""
    pass
```

## Security & Compliance Considerations

### 1. Data Privacy

**Questionnaire Data Protection**:

- Answers stored in encrypted metadata
- HIPAA compliance for medical questionnaires
- User consent tracking for research participation
- Data retention and deletion policies

### 2. Input Validation

**Choice Validation**:

```python
# Enhanced validation in tool_ask_multiple_choice
def validate_choices(choices: list[dict]) -> list[Choice]:
    """Validate and sanitize choice data."""
    for choice in choices:
        # Sanitize label text
        # Validate value format
        # Check for required fields
    return parsed_choices
```

### 3. Access Control

**Role-Based Questionnaire Access**:

```python
# In agent configuration
"allowed_questionnaires": ["zlm", "intake", "consent"]  # Restrict questionnaire access
"questionnaire_permissions": {
    "can_reset": False,
    "can_export": True,
    "can_view_history": False
}
```

## Performance Optimization

### 1. Caching Strategies

**Questionnaire State Caching**:

- Cache questionnaire configurations
- Optimize metadata lookups
- Batch answer retrievals

### 2. Frontend Optimization

**Widget Rendering Performance**:

- Lazy load choice options
- Optimize re-renders on selection
- Implement virtual scrolling for long choice lists

## Conclusion

The Multiple Choice, Questionnaire, and Noop tools form a sophisticated interaction system that enables:

1. **Rich User Interactions**: Through interactive multiple choice widgets
2. **Structured Data Collection**: Via configurable questionnaire systems
3. **Flow Control**: Using the noop tool for precise execution timing

These tools are critical for healthcare applications, user onboarding, and any scenario requiring structured user input and guided workflows. The current implementation is robust but has clear opportunities for enhancement in areas of flexibility, validation, and user experience.

The tight integration between backend tool execution, frontend widget rendering, and conversation flow control demonstrates the sophisticated architecture of the EasyLog system and provides a solid foundation for future improvements.
