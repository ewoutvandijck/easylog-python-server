# Flutter Chat Agent Comprehensive Development Guide

## 🎯 Mission Statement

This document serves as the **definitive guide** for building, maintaining, and enhancing the Apperto Flutter chat system. It's designed for seamless collaboration between:

- **Flutter Developers** (Human & AI Assistant)
- **Python Server Developers** (Python Assistant Claude 4)
- **System Architects** (All parties)

## 🏗️ Architecture Overview

### System Integration Pattern

```
Flutter App ←→ Nginx Proxy ←→ Python FastAPI Server ←→ [Neo4j, Weaviate, MySQL]
   ↓              ↓                    ↓                        ↓
Chat UI      CORS Handling      Agent Processing         Knowledge Storage
```

### Key Components

| Component | Location | Purpose | Technology |
|-----------|----------|---------|------------|
| **Flutter Chat UI** | `lib/features/chat/` | Real-time chat interface | Flutter + BLoC |
| **API Client** | `ai_chat_client/` | Generated API integration | OpenAPI + Dio |
| **Python Server** | `easylog-python-server` | Agent processing & tools | FastAPI + Python |
| **Agent System** | `apps/api/src/agents/` | Modular AI agents | Anthropic/OpenAI |

## 📱 Flutter Chat System Architecture

### 🎨 UI Layer (`lib/features/chat/presentation/`)

#### Core Components

**1. ChatWithAssistantPage (`chat_with_assistant_page.dart`)**
- **Purpose**: Main chat interface container
- **Key Features**:
  - Real-time message streaming via BLoC
  - Multi-media support (text, images, PDFs)
  - Custom bubble styling with proper alignment
  - Dynamic agent configuration switching
  - Integration with `flutter_chat_ui` package

**2. ChatInputBar (`chat_input_bar.dart`)**
- **Purpose**: Input interface with attachment support
- **Features**:
  - Text input with markdown support
  - Image/camera integration
  - File picker for documents
  - Attachment preview and management

**3. MultipleChoiceDisplay (`multiple_choice_display.dart`)**
- **Purpose**: Interactive choice widgets from Python tools
- **Integration**: Processes `tool_ask_multiple_choice` responses

### 🧠 State Management (`lib/features/chat/cubit/`)

#### AiChatCubit Architecture

**State Pattern**: `ResultState<AiChatState>`

```dart
class AiChatState {
  final List<types.Message> messages;           // Chat message history
  final Map<String, String> questionnaireAnswers; // Agent questionnaire data
  final File? selectedAttachment;               // Current attachment
  final bool isProcessing;                      // Message processing state
  final DCCError? error;                        // Error handling
}
```

**Key Methods**:

```dart
// Initialize chat thread with unique ID
init(String threadId)

// Send text message to agent
sendMessage(types.Message message, AgentConfig config, AppLocalizations l10n)

// Send attachment (image/file)
sendAttachmentMessage(AgentConfig config, AppLocalizations l10n)

// Handle real-time streaming responses
_handleMessageStream(Stream<MessageResponse> stream)

// Process different event types from Python
_handleTextDeltaEvent(TextDeltaContent content)
_handleToolResultEvent(ToolResultContent content)
```

### 🔗 API Integration (`ai_chat_client/`)

#### Auto-Generated Client Features

**Base URL**: `staging.easylog.nu/ai`

**Core Endpoints**:

```dart
// Thread Management
createThread(ThreadCreateInput input)
getThreadById(String id)
deleteThread(String id)

// Message Operations
createMessage(String threadId, MessageCreateInput input)
getMessages(String threadId, {int? limit, String? before})
deleteMessage(String threadId, String messageId)

// Knowledge Management
uploadDocument(MultipartFile file)
deleteDocument(String documentId)

// System Status
healthCheck()
getAvailableModels()
```

**Message Format**:

```dart
class MessageCreateInput {
  final MessageResponseRoleEnum role;     // user | assistant
  final List<ContentUnion> content;       // Multi-modal content
  final AgentConfig? agentConfig;         // Agent configuration
}

// Content Types
- TextContent: Plain text messages
- ImageContent: Base64 encoded images  
- FileContent: Document attachments
```

### 🎛️ Configuration System

#### Agent Configuration Structure

```dart
class AgentConfig {
  final String agentType;                 // "MUMCAgent" | "EasyLogAgent" | "DebugAgent"
  final List<RoleConfig> roles;           // Multi-persona support
  final String prompt;                    // Base system prompt
  final String model;                     // LLM model selection
  final Map<String, dynamic>? metadata;   // Custom configuration
}

class RoleConfig {
  final String name;                      // Role identifier
  final String prompt;                    // Role-specific prompt
  final String model;                     // Role-specific model
  final String toolsRegex;               // Tool access pattern
  final List<String>? allowedSubjects;   // Knowledge restrictions
  final List<QuestionConfig> questionnaire; // Dynamic questions
}
```

#### Assistant Field Integration

```dart
class AssistantFieldType {
  final String name;                      // Unique identifier
  final String label;                     // UI display name
  final AgentConfig agentConfig;          // Agent configuration
  final String? description;              // Help text
}
```

## 🐍 Python Server Integration

### 🤖 Agent Architecture

#### Available Agents

**1. MUMCAgent** - Healthcare/Medical Assistant
- **Specialization**: COPD care, medical data visualization
- **Unique Tools**: `tool_create_zlm_chart` (medical burden meter)
- **Model**: `anthropic/claude-sonnet-4`
- **Super Agent Interval**: 3 hours

**2. EasyLogAgent** - Business Intelligence Assistant  
- **Specialization**: Business analytics, project management
- **Key Tools**: SQL access, backend integration, business charts
- **Model**: `anthropic/claude-sonnet-4`
- **Super Agent Interval**: 3 hours

**3. DebugAgent** - Development Assistant
- **Specialization**: Testing, debugging, simplified workflows
- **Key Tools**: Basic questionnaires, notifications
- **Model**: `openai/gpt-4.1`
- **Super Agent Interval**: 2 hours

### 🛠️ Tool Categories & Flutter Integration

#### 1. Visualization Tools → Flutter Chart Widgets

**Charts Generated by Python → Displayed in Flutter**:

```python
# Python Agent Tools
tool_create_bar_chart()    → ChartWidget → Flutter: buildBarChartFlChart()
tool_create_line_chart()   → ChartWidget → Flutter: buildLineChart()
tool_create_zlm_chart()    → ChartWidget → Flutter: buildZLMChart()
```

**Flutter Chart Integration**:
- Location: `lib/features/chat/presentation/widgets/build_bar_chart_fl_chart.dart`
- Uses: `fl_chart` package for visualization
- Color System: Automatic color role mapping from Python

#### 2. Interactive Tools → Flutter UI Components

**Multiple Choice Widgets**:
```python
# Python Tool
tool_ask_multiple_choice(question, choices) → MultipleChoiceWidget
```

```dart
// Flutter Processing
processMultipleChoiceResponses() → MultipleChoiceDisplay widget
```

#### 3. Knowledge Management → Flutter File Handling

**Document Upload Flow**:
```dart
// Flutter Side
FilePicker.platform.pickFiles() → 
MessageCreateInputFileContent → 
API: uploadDocument() → 
Python: tool_search_documents()
```

**Image Processing Flow**:
```dart
// Flutter Side  
ImagePicker.pickImage() →
Image compression →
Base64 encoding →
MessageCreateInputImageContent →
Python: tool_download_image()
```

#### 4. Notification Integration

**Python → Flutter Push Notifications**:
```python
# Python Tool
tool_send_notification(title, contents) → OneSignal → Flutter App
```

**Flutter Notification Handling**:
- Package: `onesignal_flutter`
- Configuration: Flavor-specific setup
- Integration: Background/foreground handling

### 🔄 Real-Time Communication

#### Server-Sent Events (SSE) Streaming

**Python Server**:
```python
# Streaming response with multiple event types
yield TextDeltaContent(delta="partial text")
yield ToolResultContent(content=chart_widget)
yield ToolResultContent(content=multiple_choice_widget)
```

**Flutter Client**:
```dart
// SSE Stream handling via flutter_client_sse
Stream<MessageResponse> _messageStream = client.createMessage()
_messageStream.listen((event) {
  switch (event.content.runtimeType) {
    case TextDeltaContent: _handleTextDelta();
    case ToolResultContent: _handleToolResult();
  }
});
```

## 🎯 Complete Widget & Tool Reference

### 📊 Chart Widgets

#### **Bar Chart Widget** (`buildBarChartFlChart`)

**Python Tool**: `tool_create_bar_chart()`

**Input Configuration**:
```python
ChartWidget(
    type="bar",
    title="Chart Title",
    description="Chart Description",  # Optional
    data=[
        {"category": "A", "value": 10, "colorRole": "success"},
        {"category": "B", "value": 20, "colorRole": "warning"}
    ],
    series=[
        SeriesConfig(
            dataKey="value",
            label="Data Series",
            style=StyleConfig(
                color="#FF0000",
                strokeWidth=16,  # Bar width
                radius=4         # Border radius
            )
        )
    ],
    xAxis=AxisConfig(
        label="category",  # Data key for X-axis
        gridLines=True,
        axisLine=True
    ),
    yAxis=AxisConfig(
        gridLines=True,
        axisLine=True
    ),
    tooltip=TooltipConfig(show=True),
    animation=True,
    legend=True,  # Not yet implemented
    height=400,
    width=None    # Responsive
)
```

**Flutter Features**:
- **Dynamic Bar Width**: Automatically adjusts based on data point count
  - 1-2 items: 32px width
  - 3-4 items: 24px width  
  - 5+ items: 16px width
- **Color Parsing**: Supports hex colors with fallback to Material colors
- **Interactive Tooltips**: Shows series label and value on touch
- **Responsive Sizing**: AspectRatio 1.5 for consistent layout
- **Grid Lines**: Configurable X/Y grid visibility
- **Axis Labels**: Dynamic X-axis labels from data
- **Animation**: 250ms transition duration

**Current Limitations**:
- No stacked bar support yet
- Legend not implemented
- Only single series per bar group

#### **Line Chart Widget** (Planned)

**Python Tool**: `tool_create_line_chart()`

**Supported Types**:
```python
ChartWidgetTypeEnum.line    # → Future implementation
ChartWidgetTypeEnum.pie     # → Future implementation  
ChartWidgetTypeEnum.donut   # → Future implementation
```

#### **ZLM Chart Widget** (MUMC Agent Only)

**Python Tool**: `tool_create_zlm_chart()`

**Specialization**: Medical COPD burden meter visualization
- **Language Support**: Dutch (`nl`) and English (`en`)
- **Height**: Default 1000px for detailed medical charts
- **Data Range**: 0-100 percentage values
- **Color Scheme**: Medical-specific color coding

### 🎯 Interactive Widgets

#### **Multiple Choice Widget** (`MultipleChoiceDisplay`)

**Python Tool**: `tool_ask_multiple_choice()`

**Data Structure**:
```python
MultipleChoiceWidget(
    question="What would you like to do?",
    choices=[
        Choice(label="Option 1", value="option_1"),
        Choice(label="Option 2", value="option_2"),
        Choice(label="Option 3", value="option_3")
    ],
    type="multiple_choice"
)
```

**Flutter Implementation**:
```dart
class MultipleChoiceWidget {
  final String question;           // Question text
  final List<Choice> choices;      // Available options
  final String? selectedChoice;    // Selected value (null = not selected)
  final String type;              // Always "multiple_choice"
}

class Choice {
  final String label;             // Display text
  final String value;             // Internal value for processing
}
```

**UI Features**:
- **Visual States**: 
  - Unselected: Pastel blue background
  - Selected: Primary color background  
  - Disabled: All choices disabled after selection
- **Layout**: 80% width, left-aligned, stretched buttons
- **Color System**: Integrated with dynamic theme
- **Interaction**: Single selection, immediate state update
- **Processing**: Automatic conversion to user text message

**Processing Flow**:
1. Python sends `MultipleChoiceWidget` via `ToolResultContent`
2. Flutter displays interactive buttons
3. User selects choice → Button disabled, choice highlighted
4. Flutter sends user's choice label as text message
5. Python receives choice value for further processing

### 📷 Media Widgets

#### **Image Widget** (`ImageMessage`)

**Python Tools**:
- `tool_download_image(url)`: Download external images
- Direct base64 image content in `ToolResultContent`

**Flutter Processing**:
```dart
// URL to Image
urlToImage(url, id, role) → ImageMessage
// - Downloads from URL
// - Saves to local storage
// - Decodes for dimensions
// - Creates ImageMessage with local path

// Base64 to Image  
contentToImage(base64Content, id, role) → ImageMessage
// - Removes base64 prefix
// - Decodes to bytes
// - Saves to local file
// - Creates ImageMessage
```

**Image Features**:
- **Local Storage**: All images saved to app documents directory
- **Format Support**: JPEG, PNG, GIF, WebP, BMP
- **Compression**: Automatic compression on upload
- **Dimensions**: Auto-calculated width/height
- **Caching**: File-based caching system
- **Error Handling**: Graceful fallbacks for corrupt data

**Display Properties**:
- **User Images**: 63% of available width, right-aligned
- **Assistant Images**: 70% of available width, left-aligned
- **Border Radius**: Consistent with chat bubble styling
- **File Names**: Displayed below image if available

#### **File Widget** (`FileMessage`)

**Python Tool**: Direct file attachment support

**Supported Types**:
- **PDF Files**: Special PDF icon and preview
- **Other Files**: Generic file icon

**Flutter Implementation**:
```dart
// PDF Files
- Red-themed container with PDF icon
- Truncated filename display (max 15 chars)
- Size: 60x60px container

// Other Files  
- Secondary color container with generic file icon
- Same sizing and layout as PDF
```

### 🔄 System Widgets

#### **Loading Widget** (`CustomMessageTypes.loadingMessage`)

**Purpose**: Indicates AI processing state

**Flutter Implementation**:
```dart
CustomMessage(
  metadata: {'type': CustomMessageTypes.loadingMessage}
)
```

**Features**:
- **Animation**: Loading animation widget
- **Auto-removal**: Removed when response completes
- **Jitter Prevention**: Multiple consecutive loading messages filtered
- **Position**: Always at top of message list

#### **Text Delta Widget** (Internal)

**Purpose**: Real-time text streaming from Python

**Processing**:
```dart
_handleTextDeltaEvent(TextDeltaContent chunk) {
  // Finds existing message by ID or creates new
  // Appends delta to existing text
  // Updates UI in real-time
}
```

**Features**:
- **Incremental Updates**: Text builds character by character
- **Message Merging**: Multiple deltas combined into single message
- **Error Recovery**: Handles missing or out-of-order deltas

## 🎯 Message Processing Pipeline

### 📨 Message Flow Architecture

#### **1. User Input Processing**

**Text Messages**:
```dart
sendMessage() → MessageCreateInput → Python Agent → Response Stream
```

**Attachment Messages**:
```dart
sendAttachmentMessage() → 
Image/File Processing →
Base64 Encoding → 
MessageCreateInputFileContent/ImageContent →
Python Agent
```

#### **2. Python Response Processing**

**Content Types from Python**:
```python
# Text Content
TextContent(id, text) → Flutter TextMessage

# Text Delta Content  
TextDeltaContent(id, delta) → Streaming text updates

# Tool Result Content
ToolResultContent(
    id=message_id,
    widgetType="chart|image|multiple_choice|image_url|text",
    output=serialized_data,
    isError=false
) → CustomMessage or ImageMessage

# Tool Use Content (Internal)
ToolUseContent → Not displayed (internal agent processing)

# Image Content
ImageContent(imageUrl, id) → ImageMessage

# File Content  
FileContent(fileName) → TextMessage with file info
```

#### **3. Flutter Message Conversion**

**Core Conversion Function**: `toChatUIMessages()`

```dart
Future<List<ui.Message?>> toChatUIMessages(api.MessageResponse message) {
  // Converts Python MessageResponse to Flutter UI Messages
  // Handles all content types asynchronously
  // Returns list of UI-ready messages
}
```

**Tool Result Processing**: `toolResultContentToMessage()`

```dart
switch (trc.widgetType) {
  case multipleChoice: → CustomMessage with MultipleChoiceWidget
  case image: → ImageMessage via contentToImage()
  case chart: → CustomMessage with ChartWidget  
  case imageUrl: → ImageMessage via urlToImage()
  case text: → null (often JSON, not displayed)
}
```

### 🔄 State Management Flow

#### **Message State Updates**

```dart
// Real-time streaming
_messageStream.listen((chunk) {
  if (chunk is TextDeltaContent) {
    _handleTextDeltaEvent(chunk);  // Incremental text updates
  } else if (chunk is ToolResultContent) {
    handleToolResultEvent(chunk);   // Widget processing
  }
});
```

#### **Choice Processing**

```dart
sendChoice(messageId, multipleChoiceWidget, l10n, agentConfig) {
  // 1. Update UI immediately (highlight selected choice)
  // 2. Convert choice to TextMessage
  // 3. Handle streaming state (queue if agent is responding)
  // 4. Send choice to Python agent
}
```

#### **Pending Choice Management**

```dart
class PendingChoice {
  final Message message;
  final AppLocalizations l10n;  
  final Map<String, dynamic> agentConfig;
}

// Queues choices during streaming to prevent conflicts
_checkPendingChoice() → processes queued choice when streaming completes
```

## 🔧 Configuration Deep Dive

### 🎛️ Chart Configuration Options

#### **Chart Types**
```python
ChartWidgetTypeEnum:
  - bar      # ✅ Fully implemented
  - line     # 🔄 Planned
  - pie      # 🔄 Planned  
  - donut    # 🔄 Planned
```

#### **Axis Configuration**
```python
AxisConfig(
    label="data_key",           # Required: Data field name
    gridLines=True,            # Show grid lines
    axisLine=True,             # Show axis line
    # Future options:
    # min=0, max=100           # Axis range
    # tickInterval=10          # Tick spacing
    # rotation=45              # Label rotation
)
```

#### **Series Configuration**
```python
SeriesConfig(
    dataKey="value_field",     # Required: Data field reference
    label="Series Name",       # Display name for tooltips/legend
    style=StyleConfig(
        color="#FF0000",       # Hex color (with # prefix)
        strokeWidth=2,         # Line/bar width
        radius=4               # Border radius for bars
    )
)
```

#### **Tooltip Configuration**
```python
TooltipConfig(
    show=True,                 # Enable/disable tooltips
    customContent="Custom",    # Custom tooltip content (future)
    hideLabel=False           # Hide series labels (future)
)
```

#### **Style Configuration**
```python
StyleConfig(
    color="#HEXCOLOR",        # Primary color
    strokeWidth=2,            # Width for lines/borders
    radius=4                  # Border radius
)
```

#### **Margin Configuration**
```python
MarginConfig(
    top=20,
    right=20, 
    bottom=40,
    left=40
)
```

### 🎨 Color System

#### **Python Color Roles**
```python
DEFAULT_COLOR_ROLE_MAP = {
    "success": "#b2f2bb",     # Pastel Green
    "neutral": "#a1c9f4",     # Pastel Blue  
    "warning": "#ffb3ba",     # Pastel Red
    "info": "#FFFACD",        # LemonChiffon
    "primary": "#DDA0DD",     # Plum
    "accent": "#B0E0E6",      # PowderBlue
    "muted": "#D3D3D3",       # LightGray
}
```

#### **Flutter Color Processing**
```dart
Color _parseColor(String? colorString, Color defaultColor) {
  // Supports:
  // - "#RRGGBB" format
  // - "RRGGBB" format  
  // - Fallback to Material Design colors
  // - Error handling with defaults
}
```

### 📱 UI Customization Options

#### **Message Alignment**
```dart
// User messages (role: "user")
alignment: Alignment.centerRight
margin: EdgeInsets.only(right: _messagePadding * 2.0)
color: pastelBlue (lerped primary + white)

// Assistant messages (role: "assistant")  
alignment: Alignment.centerLeft
margin: EdgeInsets.only(left: _messagePadding * 0.5) // Text
margin: EdgeInsets.only(left: _messagePadding * 1.5) // Images/Charts
color: Colors.transparent
```

#### **Message Styling**
```dart
const _messagePadding = 16.0;

// Bubble borders
BorderRadius.circular(Sizes.m)  // Consistent border radius

// Typography
Theme.of(context).textTheme.bodyMedium  // Base text style
fontSize: 15  // Standard message text size
```

#### **Theme Integration**
```dart
// Uses dynamic theme system
context.colors.primary          // Brand primary color
context.colors.secondary5       // Input background  
context.colors.secondary100     // Input text color
context.colors.white           // Contrast text
```

## 🚀 Development Workflow

### 🔄 Feature Development Process

#### 1. Planning Phase
- [ ] Define agent requirements (tools needed, UI components)
- [ ] Update Python agent configuration
- [ ] Plan Flutter UI changes
- [ ] Design API changes if needed

#### 2. Python Server Development
- [ ] Implement new agent tools
- [ ] Update agent configuration
- [ ] Test tool functionality
- [ ] Update OpenAPI documentation

#### 3. Flutter Client Development  
- [ ] Regenerate API client: `make code_gen_chat_api`
- [ ] Update Flutter models if needed
- [ ] Implement UI components
- [ ] Update state management
- [ ] Add tests

#### 4. Integration Testing
- [ ] Test Python agent functionality
- [ ] Test Flutter UI components  
- [ ] Test real-time communication
- [ ] Test error handling
- [ ] Validate across flavors (apperto, vdh)

### 🛡️ Error Handling Strategy

#### Python Server Errors
```python
# Standard error format in Python
raise DCCError(
    message="User-friendly message",
    details="Technical details",
    error_code="SPECIFIC_CODE"
)
```

#### Flutter Error Handling
```dart
// BLoC error state management
state = state.copyWith(
  error: DCCError.fromException(exception),
  isLoading: false,
);

// UI error display
if (state.error != null) {
  showPillSnackbar(context, state.error!.message);
}
```

#### Common Error Scenarios
- **Connection Issues**: Network timeouts, server unavailable
- **Authentication**: Token expiry, unauthorized access
- **Validation**: Invalid input, missing required fields  
- **Processing**: Agent tool failures, model errors
- **File Handling**: Upload failures, format issues

### 🔧 Configuration Management

#### Environment Setup
```bash
# Flutter environment variables
--dart-define="mapsAPIKey=$MAPS_API_KEY"
--flavor apperto

# Python server configuration
OPENROUTER_API_KEY=sk-or-v1-...
ANTHROPIC_API_KEY=sk-ant-api03-...
```

#### Flavor Configuration
```dart
// Multi-tenant support
--flavor apperto -t lib/main_apperto.dart
--flavor vdh -t lib/main_vdh.dart
```

## 🎯 Advanced Development Patterns

### 🏗️ Clean Architecture Implementation

#### Layer Structure
```
lib/features/chat/
├── data/           # API clients, repositories
├── model/          # Data models, transformations  
├── cubit/          # State management (BLoC)
└── presentation/   # UI components
```

#### Dependency Flow
```
Presentation → Cubit → Repository → API Client → Python Server
```

### 🧪 Testing Strategy

#### Unit Tests
```dart
// Cubit Tests
test('should emit loading then success when sending message', () {
  // Arrange
  final cubit = AiChatCubit();
  // Act & Assert
  expectLater(cubit.stream, emitsInOrder([
    isA<ResultState>().having((s) => s.isLoading, 'isLoading', true),
    isA<ResultState>().having((s) => s.isSuccess, 'isSuccess', true),
  ]));
});
```

#### Widget Tests
```dart
// Chat UI Tests
testWidgets('should display messages correctly', (tester) async {
  await tester.pumpWidget(ChatWithAssistantPage());
  expect(find.byType(Chat), findsOneWidget);
});
```

#### Golden Tests
```dart
// Visual regression tests
testGoldens('chat_bubble_alignment', (tester) async {
  await tester.pumpWidgetBuilder(ChatBubble());
  await screenMatchesGolden(tester, 'chat_bubble_alignment');
});
```

### 🔧 Code Generation Workflow

#### Build Runner Commands
```bash
# Generate API client from Python OpenAPI
make code_gen_chat_api

# Generate Flutter code (freezed, injectable, etc.)  
make code_gen

# Update generated files
flutter packages pub run build_runner build --delete-conflicting-outputs
```

#### Auto-Generated Files
- `ai_chat_client/`: API client from OpenAPI spec
- `*.g.dart`: JSON serialization
- `*.freezed.dart`: Immutable models
- `*.gr.dart`: Auto Route navigation

### 🎨 UI/UX Guidelines

#### Theme Integration
```dart
// Use dynamic theme system
theme: DefaultChatTheme(
  primaryColor: context.colors.primary,
  secondaryColor: context.colors.secondary5,
  inputBackgroundColor: context.colors.secondary5,
)
```

#### Message Alignment System
```dart
// User messages: right-aligned with pastel blue
// Assistant messages: left-aligned with transparent background
final isUser = message.author.id == MessageResponseRoleEnum.user.name;
alignment: isUser ? Alignment.centerRight : Alignment.centerLeft
```

#### Responsive Design
```dart
// Consistent padding system
const _messagePadding = 16.0;
// Size constants from core theming
Sizes.s, Sizes.m, Sizes.l, Sizes.xl
```

## 🎯 Success Metrics & Monitoring

### 📊 Key Performance Indicators

#### Flutter App Metrics
- **Message Delivery Time**: < 2 seconds for text, < 5 seconds for attachments
- **UI Responsiveness**: Smooth 60fps scrolling
- **Error Rate**: < 1% for message sending
- **Crash Rate**: < 0.1% during chat sessions

#### Python Server Metrics
- **Agent Response Time**: < 10 seconds for complex tool usage
- **Tool Success Rate**: > 95% for all tool executions
- **Memory Usage**: Stable over extended conversations
- **Concurrent Users**: Support 100+ simultaneous chats

### 🔍 Monitoring Commands

#### Flutter Debugging
```bash
# Run with debug logging
make run_apperto

# Analyze performance
flutter analyze
flutter test --coverage
```

#### Python Server Monitoring
```bash
# Live logs monitoring
ssh easylog-python "docker logs easylog-python-server.api -f"

# Agent-specific monitoring
ssh easylog-python "docker logs easylog-python-server.api | grep 'MUMCAgent\|EasyLogAgent'"

# Error monitoring
ssh easylog-python "docker logs easylog-python-server.api --tail 100 | grep -i error"
```

## 🤝 Collaboration Guidelines

### 👥 Role Responsibilities

#### Flutter Developer (Human + AI Assistant)
- **UI/UX Implementation**: Chat interface, widgets, animations
- **State Management**: BLoC implementation, error handling
- **API Integration**: Client generation, request/response handling
- **Testing**: Unit, widget, and integration tests
- **Performance**: Optimization, memory management

#### Python Developer (Python Assistant Claude 4)
- **Agent Development**: Tool creation, configuration
- **API Design**: Endpoint specification, data models
- **Knowledge Management**: Document processing, search
- **Integration**: Database connections, external services
- **Monitoring**: Logging, error tracking, performance

#### System Architect (All Parties)
- **Architecture Decisions**: Technology choices, patterns
- **Integration Planning**: Cross-system communication
- **Security**: Authentication, authorization, data protection
- **Scalability**: Performance optimization, resource management

### 📋 Communication Protocols

#### Issue Reporting Format
```markdown
**Component**: Flutter Chat UI / Python Agent / API Integration
**Severity**: Critical / High / Medium / Low
**Description**: Brief description of the issue
**Steps to Reproduce**: 
1. Step one
2. Step two
**Expected Behavior**: What should happen
**Actual Behavior**: What actually happens
**Environment**: Flavor, device, server version
**Logs**: Relevant log excerpts
```

#### Feature Request Format
```markdown
**Feature Name**: Descriptive name
**Component**: Flutter / Python / Both
**User Story**: As a [user type], I want [goal] so that [benefit]
**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2
**Technical Requirements**:
- Python tools needed
- Flutter UI changes
- API modifications
**Priority**: High / Medium / Low
```

### 🎯 Definition of Done

#### For New Features
- [ ] Python agent tools implemented and tested
- [ ] Flutter UI components created
- [ ] API client updated
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Performance benchmarks met
- [ ] Error handling implemented
- [ ] Accessibility guidelines followed

#### For Bug Fixes
- [ ] Root cause identified
- [ ] Fix implemented with minimal scope
- [ ] Regression tests added
- [ ] Manual testing completed
- [ ] No new issues introduced
- [ ] Documentation updated if needed
- [ ] Monitoring confirms resolution

## 🔮 Future Enhancements

### 🚀 Planned Features

#### Short Term (Next Sprint)
- **Voice Messages**: Audio recording and playback
- **Message Reactions**: Emoji reactions to agent responses
- **Conversation Search**: Full-text search within chat history
- **Offline Support**: Basic functionality without internet

#### Medium Term (Next Quarter)
- **Multi-Agent Conversations**: Multiple agents in single chat
- **Advanced Attachments**: Video, audio, document preview
- **Custom Themes**: User-customizable chat appearance  
- **Analytics Dashboard**: Chat usage and performance metrics

#### Long Term (Future Roadmap)
- **AI-Powered Suggestions**: Smart reply suggestions
- **Real-Time Collaboration**: Multiple users in shared chats
- **Advanced Security**: End-to-end encryption
- **Platform Expansion**: Web, desktop versions

### 🔧 Technical Debt & Improvements

#### Code Quality
- [ ] Migrate to latest Flutter version
- [ ] Improve test coverage to >90%
- [ ] Refactor large widgets into smaller components
- [ ] Implement stricter linting rules

#### Performance
- [ ] Optimize image loading and caching
- [ ] Implement message virtualization for large conversations
- [ ] Reduce memory usage in long chat sessions
- [ ] Improve initial load time

#### Developer Experience
- [ ] Automated code generation pipeline
- [ ] Better debugging tools and logging
- [ ] Comprehensive development documentation
- [ ] Streamlined setup process for new developers

---

## 📚 Quick Reference

### Essential Commands
```bash
# Development
make run_apperto                    # Run Flutter app
make code_gen_chat_api             # Update API client
make code_gen                      # Generate Flutter code

# Testing  
make tests                         # Run Flutter tests
make update_goldens               # Update golden tests

# Monitoring
ssh easylog-python "docker logs easylog-python-server.api -f"
```

### Key Files
```
lib/features/chat/
├── presentation/chat_with_assistant_page.dart    # Main chat UI
├── cubit/ai_chat_cubit.dart                     # State management
└── model/ai_message.dart                        # Message models

ai_chat_client/                                   # Generated API client
memory-bank/knowledge/APPERTO.md                 # Flutter architecture guide
```

### Important URLs
- **Production API**: `https://staging.easylog.nu/ai`
- **API Documentation**: `https://staging.easylog.nu/ai/docs`
- **Server Monitoring**: SSH access to `easylog-python`

---

> **Remember**: This is a living document. Update it as the system evolves to ensure it remains the definitive guide for successful collaboration and development. 