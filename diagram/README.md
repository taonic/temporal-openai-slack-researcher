# Agent Workflow Diagram

```mermaid
flowchart TD
    A["User Input"] --> B["Plan Agent<br/>Creates search plan"]
    B --> C{"Need Human<br/>Input?"}
    C -->|Yes| D["Return Clarifying<br/>Questions"]
    C -->|No| E["Plan Evaluation<br/>Agent"]
    E --> F{"Plan<br/>Approved?"}
    F -->|No| B
    F -->|Yes| G["Execution Agent<br/>Searches Slack"]
    G --> H["Generate Report"]
    H --> I["Final Output"]
    
    style A fill:#e1f5fe
    style I fill:#c8e6c9
    style C fill:#fff3e0
    style F fill:#fff3e0
```

## Workflow Components

### Main Flow
1. **User Input**: User asks a question about Slack conversations
2. **Plan Agent**: Creates search strategy and identifies relevant channels
3. **Human Input Check**: Returns clarifying questions if query is ambiguous
4. **Plan Evaluation**: Reviews and validates the search plan
5. **Execution Agent**: Performs Slack searches and analyzes results
6. **Final Output**: Returns structured report with findings

### Key Features
- **Smart Planning**: Converts queries into targeted search strategies
- **Channel Selection**: Identifies relevant Slack channels automatically
- **Dual Search**: Performs both global and channel-specific searches
- **Structured Reports**: Returns findings in organized Markdown format
