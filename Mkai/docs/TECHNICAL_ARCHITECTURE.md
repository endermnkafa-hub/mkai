# Technical Architecture Document

## Document Status
- Version: 0.1
- Status: Draft for review
- Purpose: Define the technical architecture for MKAI before implementation begins

## 1. Architecture Vision
MKAI will be built as a modular, scalable, and future-proof AI operating system.

The architecture must support:
- Multiple AI providers and models
- Automatic intelligent routing
- Short-term and long-term memory
- Tools, web search, and plugins
- Debug/Developer transparency
- Privacy-first user controls
- Future multimodal expansion

## 2. Architecture Principles
1. Modularity over monolithism
2. Provider abstraction over hard-coded integrations
3. Clear separation of concerns
4. Privacy and user control as first-class design constraints
5. Local-first and cloud-capable deployment model
6. Observable systems with transparent debugging
7. Replaceable components without core redesign

## 3. High-Level System Overview
MKAI will consist of the following major layers:

- Client / UI layer
- API layer
- Orchestration layer
- Intelligence layer
- Provider layer
- Memory layer
- Tool and plugin layer
- Storage and observability layer

## 4. Core Components
### 4.1 Client / UI Layer
Responsibilities:
- Render chat and assistant experience
- Handle user inputs and attachments
- Display responses, memory status, and debug information
- Support settings for memory, language, provider, and mode

### 4.2 API Layer
Responsibilities:
- Expose endpoints for chat, memory, settings, tools, and debug views
- Validate requests and responses
- Enforce authentication and authorization where needed
- Support future web, desktop, and mobile clients

### 4.3 Orchestration Layer
Responsibilities:
- Accept user requests
- Build the execution plan
- Determine whether to use memory, search, tools, or multiple models
- Route to the appropriate provider/model
- Aggregate results into a final response

This layer is the brain of MKAI.

To support the product vision, the orchestration layer will include:
- Intent detection
- Core Brain controller
- Planner module
- Decision Engine
- Skill selection engine
- Persona Engine
- Workspace selection and context binding
- Context Engine
- Model router
- Tool and web-search routing
- Judge / verifier module
- Learning feedback loop

### 4.4 Intelligence Layer
Responsibilities:
- Determine task intent
- Decide whether clarification is needed
- Decide whether web search is required
- Decide whether multi-model comparison is useful
- Decide which explanation style to use

### 4.5 Provider Layer
Responsibilities:
- Abstract communication with AI providers
- Normalize provider responses
- Handle provider-specific request formatting
- Support fallback and retries
- Support interchangeable providers and models
- Support multiple models in parallel for comparison and verification when needed

Supported provider categories include:
- Local/private: Ollama
- Cloud general intelligence: OpenAI, Anthropic, Gemini, DeepSeek, OpenRouter

### 4.6 Memory Layer
Responsibilities:
- Store and retrieve short-term, long-term, project, and temporary memories
- Decide which memories are relevant for a request
- Handle memory privacy and expiration policies
- Support memory review, editing, and deletion
- Bind memory retrieval to the active workspace

Memory types:
- Short-term memory: current session context
- Long-term memory: persistent user preferences and useful facts
- Project memory: tasks, goals, and context for active workstreams
- Temporary memory: short-lived working memory

### 4.7 Tool and Plugin Layer
Responsibilities:
- Provide structured tool execution for tasks like web search, file processing, code execution, calendars, and external services
- Keep tools modular and interchangeable
- Ensure user permission for sensitive actions

### 4.8 Storage and Observability Layer
Responsibilities:
- Persist conversations, memory, settings, and logs
- Enable debugging and development visibility
- Track latency, provider failures, tool usage, and model selection

## 5. Key Design Patterns
### 5.1 Provider Abstraction
All providers will implement a common interface so that:
- Providers are swappable
- Models are swappable
- New providers can be added without changing the core orchestration flow

### 5.2 Routing Engine
A routing engine will decide:
- Which provider/model to use
- Whether to use one model or several
- Whether to use web search or tools
- Whether a fallback is needed

Routing decisions should be based on:
- Task type
- Desired quality
- Latency requirements
- Privacy requirements
- Availability
- Cost
- Confidence

### 5.3 Memory Subsystem
The memory system should be explicit and transparent.
It should support:
- Memory capture
- Memory retrieval
- Memory review
- Memory edit/delete
- Memory disable/enable

### 5.4 Debug / Developer Mode
Debug Mode should expose:
- Selected provider and model
- Why the model was chosen
- Whether models were compared
- Web search and tool usage
- Memory retrieval summary
- Confidence level
- Timing and latency
- Errors and fallback information

It should not expose internal reasoning traces.

## 5.5 Skill Architecture
MKAI should use a skill framework rather than embedding every task directly into the assistant core.

Each skill should have:
- A clear purpose and scope
- Its own prompt strategy
- Its own tool preferences
- Access to relevant memory and workspace context
- Optional model routing preferences

Examples include Coding Skill, Research Skill, Planning Skill, Minecraft Skill, Writing Skill, Translation Skill, and Automation Skill.

## 5.6 Persona Engine
The Persona Engine should shape response style dynamically based on learned user traits and preferences.

It should use:
- User communication style preferences
- Domain preferences
- Response length preferences
- Tone preferences
- Language preferences

This allows MKAI to adapt to the user instead of forcing the user to adapt to MKAI.

## 5.7 Workspace Architecture
MKAI should support a multi-workspace model.

Each workspace should have:
- Independent conversation history
- Independent memory
- Independent goals
- Independent project context
- Independent permissions where needed
- Files and project assets
- Prompts and coding style guidance
- Plugin state and terminal history

## 5.8 Context Engine
The Context Engine should infer missing context automatically before execution.

It should resolve:
- Which workspace is active
- Which project is referenced
- Which file or code area is relevant
- Which terminal state matters
- Which previous conversation is relevant

## 5.9 Plugin Architecture
Plugins should be first-class extensions that can be added without changing MKAI core.

Each plugin should be packaged with:
- manifest.json
- permissions definition
- command definitions
- API integration layer
- settings schema
- lifecycle hooks

Plugins should be able to interact with file systems, web services, terminals, and other tools while remaining isolated and permission-controlled.

## 5.10 Confidence and Knowledge Graph
The architecture should support a knowledge graph and confidence reporting.

Confidence reporting should include:
- Confidence score
- Reasons for confidence
- Source and memory contribution summary

The knowledge graph should connect entities and relationships so MKAI can reason over a richer personal knowledge model.

## 5.11 Automation and Agent Mode
MKAI should support an automation layer and an Agent Mode.

Automation should allow safe execution of tasks such as:
- File creation and movement
- Code generation
- Running terminal commands
- Launching applications
- Running build tasks
- Creating commits

Agent Mode should provide a multi-step execution loop:
1. Understand the task
2. Plan the actions
3. Execute the actions
4. Read results or errors
5. Retry or adjust
6. Finish the task without asking repeatedly

This mode should be permission-aware and transparent.

## 5.12 Knowledge Base and Goal System
The system should include a structured knowledge base and a goal system.

Knowledge base capabilities should support:
- Project-based memory
- Personal notes and knowledge areas
- Context separation between projects
- Relevant memory retrieval for each project

Goal system capabilities should support:
- Creating and tracking goals
- Progress state
- Next action recommendation
- Last activity tracking
- Goal completion states

## 5.13 Scheduler and Self-Evaluation
The architecture should support:
- Reminders and scheduled tasks
- Periodic background actions
- Self-evaluation before final answer generation

Self-evaluation should allow the orchestration layer to ask:
- Is this answer correct?
- Can it be improved?
- Should I verify it?
- Should I search the web?
- Should I ask another model?

## 6. Data Model Concepts
### Conversations
- Conversation identifier
- Participant metadata
- Timestamp history
- Message list

### Messages
- Role: user, assistant, system, tool, tool result
- Content type: text, image, file, voice, structured data
- Metadata: timestamp, model used, source, confidence

### Memories
- Memory identifier
- Memory type: short-term, long-term, project, temporary
- Content
- Confidence or importance score
- Visibility and privacy flags
- Timestamp
- Source and expiration policy

### Tools and Plugins
- Tool identifier
- Input schema
- Output schema
- Permission level
- Availability status

## 7. Execution Flow
A typical request flow will look like this:
1. User submits a message or attachment
2. API receives the request
3. Orchestrator analyzes the task
4. Memory retrieval is considered
5. Routing engine selects provider/model strategy
6. Tools or web search may be invoked
7. One or multiple providers may respond
8. Results are compared and synthesized if needed
9. Final answer is returned to the user
10. Relevant context is stored in memory if allowed

## 8. Privacy and Security Architecture
Privacy is a core requirement.

The architecture must support:
- Local/private inference where needed
- Explicit consent for sensitive memory capture
- Memory controls for enable/disable/edit/delete
- Clear boundaries for what is persisted and what is ephemeral
- Auditability through logs and debug views

## 9. Scalability and Future-Proofing
The architecture should support:
- Local development and local inference
- Cloud-based high-quality inference
- Future plugin ecosystems
- Multimodal expansion
- Additional tools and integrations
- Distributed or multi-service growth over time

## 10. Deployment Model
### Initial Deployment
- Local-first development environment
- Backend service running locally
- Optional cloud provider integration
- SQLite or simple local storage for early milestones

### Later Phases
- More robust persistence layer
- Optional vector store for memory retrieval
- Background services for memory management and tool execution
- Possible hosted deployment for remote use

## 11. Technical Risks and Mitigations
### Risk: Provider inconsistency
Mitigation: standard provider interface and response normalization

### Risk: Memory quality issues
Mitigation: selective memory capture, review tools, expiration policies, and privacy controls

### Risk: Over-complex orchestration
Mitigation: start with a stable assistant experience and add advanced routing gradually

### Risk: Debug transparency becoming too noisy
Mitigation: separate normal mode from Developer/Debug Mode

## 12. Implementation Principles for Phase 1
The first implementation phase should prioritize:
- Stable chat quality
- Reliable provider abstraction
- Clear memory model
- Simple but useful routing
- Clean debug visibility
- A modular codebase that can grow
