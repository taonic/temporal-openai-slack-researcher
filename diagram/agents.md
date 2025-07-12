# Agent Workflow Diagram

```mermaid
flowchart TD
    A[User Input] --> B[ConversationWorkflow.process_user_message]
    B --> C[Add to chat_history and input_items]
    C --> D[Start _run_with_evaluation]
    
    D --> E[Plan Phase Loop<br/>max_evaluation_loops = 3]
    E --> F[Run Plan Agent]
    F --> G[Generate Plan]
    G --> H[Add plan to chain_of_thoughts]
    H --> I[Run Plan Evaluation Agent]
    I --> J{Plan Evaluation<br/>Passed?}
    
    J -->|No & evaluation_enabled| K[Add feedback to plan_input]
    K --> L{Max loops<br/>reached?}
    L -->|No| F
    L -->|Yes| M[Proceed to Execution]
    
    J -->|Yes or evaluation_disabled| M[Proceed to Execution]
    
    M --> N[Execution Phase Loop<br/>max_evaluation_loops = 3]
    N --> O[Add execution message to chain_of_thoughts]
    O --> P[Run Execution Agent]
    P --> Q[Execute Plan]
    Q --> R[Run Execution Evaluation Agent]
    R --> S{Execution Evaluation<br/>Passed?}
    
    S -->|No & evaluation_enabled| T[Add feedback to exec_input]
    T --> U{Max loops<br/>reached?}
    U -->|No| P
    U -->|Yes| V[Return exec_result]
    
    S -->|Yes or evaluation_disabled| V[Return exec_result]
    
    V --> W[Build Chat History]
    W --> X[Update input_items]
    X --> Y[Set Workflow Details]
    Y --> Z[Return Final Output]
    
    subgraph "Agents"
        AA[Plan Agent<br/>init_plan_agent]
        BB[Execution Agent<br/>init_execution_agent]
        CC[Plan Eval Agent<br/>init_plan_eval_agent]
        DD[Execution Eval Agent<br/>init_execution_eval_agent]
    end
    
    subgraph "Data Structures"
        EE[chat_history: list[str]]
        FF[chain_of_thoughts: list[str]]
        GG[input_items: list]
        HH[RunResult]
    end
    
    subgraph "Configuration"
        II[evaluation_enabled: bool = True]
        JJ[max_evaluation_loops: int = 3]
        KK[RunConfig with trace settings]
    end
    
    style A fill:#e1f5fe
    style Z fill:#c8e6c9
    style J fill:#fff3e0
    style S fill:#fff3e0
    style AA fill:#f3e5f5
    style BB fill:#f3e5f5
    style CC fill:#f3e5f5
    style DD fill:#f3e5f5
```

## Workflow Components

### Main Flow
1. **User Input Processing**: Receives user message and adds to chat history
2. **Plan Phase**: Generates and evaluates research plan with feedback loops
3. **Execution Phase**: Executes plan and evaluates results with feedback loops
4. **Output Generation**: Builds final chat history and returns response

### Agents
- **Plan Agent**: Creates research plans based on user input
- **Execution Agent**: Executes the approved research plan
- **Plan Evaluation Agent**: Reviews and provides feedback on plans
- **Execution Evaluation Agent**: Reviews and validates execution results

### Key Features
- **Evaluation Loops**: Up to 3 iterations for both planning and execution phases
- **Feedback Integration**: Failed evaluations trigger refinement cycles
- **Tracing**: Built-in observability with Temporal workflow tracing
- **State Management**: Maintains chat history and chain of thoughts throughout the process
