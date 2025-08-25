# Level 6 — Multi-Agent Communication: Advanced AI Workflows

**🎯 Challenge Points: 25 points (Advanced AI Level)**  
*Master sophisticated AI agent coordination and collaborative intelligence*

## 🎓 Learning Objective
Learn advanced AI orchestration patterns, agent-to-agent communication, and collaborative AI workflows. Build systems where multiple AI agents work together to solve complex problems that no single agent could handle alone.

## 📋 What You're Building
A sophisticated multi-agent system where specialized AI agents collaborate to perform complex code analysis. Agents communicate through structured protocols, share tools and context, and coordinate their work to produce comprehensive results that exceed what any individual agent could achieve.

## 🧠 Why Multi-Agent Systems Matter for AI
Single AI agents have limitations that multi-agent systems overcome:
- **Specialization**: Each agent focuses on specific expertise (security, documentation, testing)
- **Parallel Processing**: Multiple agents work simultaneously on different aspects
- **Quality Assurance**: Agents can review and validate each other's work
- **Comprehensive Analysis**: Complex problems get multi-perspective solutions
- **Fault Tolerance**: If one agent fails, others can continue working

## 🛠️ Step-by-Step Implementation Guide

### Step 1: Understanding Multi-Agent Architecture
Study the existing implementation in `src/functions/bp_multi_agent.py`:

```
📝 Code Input → 🎯 Orchestrator → 👥 Agent Registry → 🔄 Agent Coordination
                      ↓                             ↓
🤝 Message Bus ← 📊 State Management ← 🛠️ Tool Sharing ← ⚡ Parallel Execution
                      ↓                             ↓
📋 Final Report ← 🔍 Result Aggregation ← 🛡️ Guardrails ← 📈 Progress Tracking
```

The multi-agent workflow follows this sophisticated pattern:
1. **Agent Registry**: Catalog available agents and their capabilities
2. **Workflow Orchestration**: Coordinate agent interactions and task distribution
3. **Message Passing**: Enable structured communication between agents
4. **Tool Coordination**: Share resources and prevent conflicts
5. **Guardrail Enforcement**: Prevent infinite loops and inappropriate content
6. **Result Synthesis**: Combine agent outputs into comprehensive reports

### Step 2: Agent Specialization and Capabilities

#### Agent Types and Responsibilities:
```python
AGENT_CAPABILITIES = {
    "code_reviewer": {
        "specializations": ["security", "performance", "best_practices"],
        "tools": ["static_analysis", "vulnerability_scan", "complexity_metrics"],
        "max_concurrent": 2
    },
    "documentation_agent": {
        "specializations": ["api_docs", "user_guides", "code_comments"],
        "tools": ["doc_generator", "example_creator", "style_checker"],
        "max_concurrent": 1
    },
    "testing_agent": {
        "specializations": ["unit_tests", "integration_tests", "test_strategy"],
        "tools": ["test_generator", "coverage_analyzer", "mock_creator"],
        "max_concurrent": 3
    }
}
```

#### Agent Communication Protocols:
```python
class AgentMessage:
    """Structured message format for agent communication."""
    def __init__(self, 
                 sender: str, 
                 recipient: str, 
                 message_type: str, 
                 content: dict, 
                 correlation_id: str):
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type  # "request", "response", "notification"
        self.content = content
        self.correlation_id = correlation_id
        self.timestamp = datetime.utcnow().isoformat()

# Message types
MESSAGE_TYPES = {
    "task_assignment": "Assign specific work to an agent",
    "tool_request": "Request access to a shared tool",
    "context_sharing": "Share analysis results with other agents",
    "validation_request": "Ask another agent to review work",
    "completion_notification": "Signal task completion"
}
```

### Step 3: Orchestrator Implementation Deep Dive

#### Multi-Agent Coordination Pattern:
```python
@bp.orchestration_trigger(context_name="context")
def multi_agent_orchestrator(context: df.DurableOrchestrationContext) -> Generator[Any, Any, dict]:
    """Coordinate multiple AI agents for comprehensive code analysis."""
    payload = context.get_input() or {}
    
    # Phase 1: Initialize agent registry and workflow state
    agent_registry = yield context.call_activity("initialize_agent_registry", payload)
    workflow_state = {
        "agents": agent_registry,
        "tasks": [],
        "results": {},
        "iteration": 0,
        "max_iterations": MAX_AGENT_ITERATIONS
    }
    
    # Phase 2: Agent task distribution
    while workflow_state["iteration"] < workflow_state["max_iterations"]:
        # Determine next tasks based on current state
        pending_tasks = yield context.call_activity("plan_next_tasks", workflow_state)
        
        if not pending_tasks:
            break  # All work completed
            
        # Phase 3: Parallel agent execution with communication
        agent_tasks = []
        for task in pending_tasks:
            agent_tasks.append(
                context.call_activity("execute_agent_task", {
                    "task": task,
                    "workflow_state": workflow_state,
                    "correlation_id": context.instance_id
                })
            )
        
        # Wait for all agents to complete their tasks
        agent_results = yield context.task_all(agent_tasks)
        
        # Phase 4: Update workflow state with results
        workflow_state = yield context.call_activity("update_workflow_state", {
            "current_state": workflow_state,
            "agent_results": agent_results
        })
        
        workflow_state["iteration"] += 1
    
    # Phase 5: Final result synthesis
    final_report = yield context.call_activity("synthesize_final_report", workflow_state)
    
    return final_report
```

### Step 4: Agent Activity Implementation

#### Individual Agent Execution:
```python
@bp.activity_trigger(input_name="data")
async def execute_agent_task(data: str) -> dict:
    """Execute a specific agent task with communication capabilities."""
    data_dict = json.loads(data) if isinstance(data, str) else data
    
    task = data_dict["task"]
    agent_type = task["agent_type"]
    correlation_id = data_dict["correlation_id"]
    
    try:
        # Initialize agent with specialized capabilities
        agent = await create_specialized_agent(agent_type)
        
        # Execute the agent's specific task
        if agent_type == "code_reviewer":
            result = await perform_code_review(agent, task, correlation_id)
        elif agent_type == "documentation_agent":
            result = await generate_documentation(agent, task, correlation_id)
        elif agent_type == "testing_agent":
            result = await design_tests(agent, task, correlation_id)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Apply guardrails to agent output
        filtered_result, guardrail_issues = _apply_guardrails(
            result.get("output", ""),
            token_limit=AGENT_TOKEN_LIMIT,
            enable_filter=ENABLE_CONTENT_FILTER
        )
        
        return {
            "agent_type": agent_type,
            "task_id": task["id"],
            "status": "completed",
            "output": filtered_result,
            "guardrail_issues": guardrail_issues,
            "correlation_id": correlation_id
        }
        
    except Exception as e:
        logging.error("Agent task failed: %s", e, exc_info=True)
        return {
            "agent_type": agent_type,
            "task_id": task.get("id", "unknown"),
            "status": "failed",
            "error": str(e),
            "correlation_id": correlation_id
        }
```

#### Specialized Agent Implementations:
```python
async def perform_code_review(agent, task, correlation_id: str) -> dict:
    """Code review agent with security and performance focus."""
    code = task["content"]["code"]
    
    # Multi-step analysis
    security_analysis = await agent.analyze_security_issues(code)
    performance_analysis = await agent.analyze_performance(code)
    best_practices = await agent.check_best_practices(code)
    
    # Agent communication: Share findings with documentation agent
    await send_agent_message(
        sender="code_reviewer",
        recipient="documentation_agent",
        message_type="context_sharing",
        content={
            "security_findings": security_analysis,
            "performance_notes": performance_analysis
        },
        correlation_id=correlation_id
    )
    
    return {
        "output": {
            "security_score": security_analysis.get("score", 0),
            "performance_score": performance_analysis.get("score", 0),
            "recommendations": best_practices.get("recommendations", []),
            "issues_found": len(security_analysis.get("issues", []))
        }
    }

async def generate_documentation(agent, task, correlation_id: str) -> dict:
    """Documentation agent that incorporates review findings."""
    code = task["content"]["code"]
    
    # Check for context from other agents
    shared_context = await get_shared_context(correlation_id, "code_reviewer")
    
    # Generate comprehensive documentation
    api_docs = await agent.generate_api_documentation(code)
    usage_examples = await agent.create_usage_examples(code)
    
    # Incorporate security and performance notes if available
    if shared_context:
        security_notes = shared_context.get("security_findings", {})
        if security_notes.get("issues"):
            api_docs += "\n\n## Security Considerations\n"
            api_docs += agent.format_security_documentation(security_notes)
    
    return {
        "output": {
            "documentation": api_docs,
            "examples": usage_examples,
            "context_incorporated": bool(shared_context)
        }
    }

async def design_tests(agent, task, correlation_id: str) -> dict:
    """Testing agent that creates comprehensive test suites."""
    code = task["content"]["code"]
    
    # Generate test strategy
    unit_tests = await agent.generate_unit_tests(code)
    edge_cases = await agent.identify_edge_cases(code)
    mocks_needed = await agent.identify_mocking_requirements(code)
    
    # Request validation from code reviewer
    await send_agent_message(
        sender="testing_agent",
        recipient="code_reviewer",
        message_type="validation_request",
        content={"proposed_tests": unit_tests},
        correlation_id=correlation_id
    )
    
    return {
        "output": {
            "unit_tests": unit_tests,
            "edge_cases": edge_cases,
            "mocks_required": mocks_needed,
            "test_coverage_estimate": 85  # AI-estimated coverage
        }
    }
```

### Step 5: Guardrails and Safety Systems

#### Comprehensive Guardrail Implementation:
```python
def _apply_guardrails(code: str, *, token_limit: int = AGENT_TOKEN_LIMIT, enable_filter: bool = ENABLE_CONTENT_FILTER) -> tuple[str, list[str]]:
    """Apply comprehensive guardrails to agent outputs."""
    issues: list[str] = []
    
    # Token/length limits to prevent excessive output
    max_chars = max(256, token_limit * 4)
    if len(code) > max_chars:
        issues.append(f"output_truncated:{len(code)}->{max_chars}")
        code = code[:max_chars] + "\n... [output truncated for safety]"
    
    # Content filtering for inappropriate material
    if enable_filter:
        banned_patterns = [
            r"DROP\s+TABLE",           # SQL injection patterns
            r"rm\s+-rf",               # Destructive commands
            r"BEGIN\s+RSA\s+PRIVATE",  # Private key exposure
            r"AKIA[0-9A-Z]{16}",       # AWS access key pattern
            r"password\s*=\s*['\"][^'\"]+['\"]"  # Hardcoded passwords
        ]
        
        for pattern in banned_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(f"content_filter:blocked_{pattern[:20]}")
                code = re.sub(pattern, "[REDACTED_FOR_SECURITY]", code, flags=re.IGNORECASE)
    
    # Infinite loop detection in agent communication
    if "while True:" in code and "break" not in code:
        issues.append("potential_infinite_loop")
        
    # Recursive call depth limits
    recursion_depth = code.count("def ") * code.count("return ")
    if recursion_depth > 50:
        issues.append("excessive_recursion_complexity")
    
    return code, issues

# Circuit breaker for agent failures
class AgentCircuitBreaker:
    """Prevent cascading failures in multi-agent systems."""
    
    def __init__(self, failure_threshold: int = 3, timeout_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def can_execute(self) -> bool:
        """Check if agent execution should proceed."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True
    
    def record_success(self):
        """Record successful agent execution."""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed agent execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
```

## ✅ Acceptance Criteria
Complete when you can verify:
- ✅ Multiple specialized agents can work on different aspects of code analysis
- ✅ Agents communicate through structured message protocols
- ✅ Tool sharing and resource coordination prevents conflicts
- ✅ Guardrails prevent infinite loops, excessive output, and inappropriate content
- ✅ Circuit breaker protects against cascading failures
- ✅ Workflow orchestration manages agent lifecycle effectively
- ✅ Results are synthesized into comprehensive reports
- ✅ All agent interactions are logged with correlation IDs
- ✅ System handles agent failures gracefully without stopping the workflow

## 🧪 Testing the Multi-Agent System

### Cloud Testing with Deployed Functions:

1. **Deploy and test the orchestration:**
   ```bash
   # Deploy to Azure
   azd up
   
   # Start the orchestration
   curl -X POST https://your-function-app.azurewebsites.net/api/orchestrators/multi-agent \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $YOUR_TOKEN" \
     -d '{
       "projectId": "test-project",
       "snippetId": "complex_api.py",
       "workflow": "comprehensive-analysis",
       "content": {
         "code": "class UserAPI:\n    def __init__(self, db_connection):\n        self.db = db_connection\n    \n    async def create_user(self, user_data: dict) -> dict:\n        if not user_data.get(\"email\"):\n            raise ValueError(\"Email required\")\n        \n        user_id = str(uuid.uuid4())\n        await self.db.execute(\n            \"INSERT INTO users (id, email, data) VALUES (?, ?, ?)\",\n            (user_id, user_data[\"email\"], json.dumps(user_data))\n        )\n        return {\"id\": user_id, \"status\": \"created\"}"
       }
     }'
   ```

2. **Monitor orchestration progress:**
   ```bash
   # Check status using the returned instanceId
   curl "https://your-function-app.azurewebsites.net/runtime/webhooks/durabletask/instances/{instanceId}" \
     -H "Authorization: Bearer $YOUR_TOKEN"
   ```

3. **Expected agent workflow:**
   ```
   [Agent Registry] → Code Reviewer starts security analysis
                   → Documentation Agent waits for context
                   → Testing Agent begins test design
   
   [Communication] → Code Reviewer shares security findings
                  → Documentation Agent incorporates security notes
                  → Testing Agent requests validation
   
   [Synthesis] → All results combined into comprehensive report
   ```

### Test Multi-Agent Communication:

```bash
# Test with more complex code requiring extensive collaboration
curl -X POST https://your-function-app.azurewebsites.net/api/orchestrators/multi-agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $YOUR_TOKEN" \
  -d '{
    "projectId": "advanced-project",
    "snippetId": "payment_processor.py",
    "workflow": "security-focused-analysis",
    "content": {
      "code": "class PaymentProcessor:\n    def __init__(self, api_key: str, webhook_secret: str):\n        self.api_key = api_key\n        self.secret = webhook_secret\n        self.client = PaymentClient(api_key)\n    \n    async def process_payment(self, amount: float, card_token: str) -> dict:\n        if amount <= 0:\n            raise ValueError(\"Invalid amount\")\n        \n        try:\n            result = await self.client.charge(\n                amount=int(amount * 100),  # Convert to cents\n                source=card_token,\n                currency=\"usd\"\n            )\n            \n            # Log transaction\n            logging.info(f\"Payment processed: {result.id} for ${amount}\")\n            \n            return {\n                \"transaction_id\": result.id,\n                \"status\": \"success\",\n                \"amount\": amount\n            }\n        except PaymentError as e:\n            logging.error(f\"Payment failed: {e}\")\n            raise\n    \n    def verify_webhook(self, payload: str, signature: str) -> bool:\n        expected = hmac.new(\n            self.secret.encode(),\n            payload.encode(),\n            hashlib.sha256\n        ).hexdigest()\n        return hmac.compare_digest(expected, signature)"
    }
  }'
```

### Expected Multi-Agent Analysis Results:

```json
{
  "workflow_id": "abc123",
  "status": "completed",
  "agents_involved": ["code_reviewer", "documentation_agent", "testing_agent"],
  "analysis_results": {
    "security_analysis": {
      "score": 85,
      "issues": [
        "API key stored in constructor - consider using environment variables",
        "Logging may expose sensitive transaction data"
      ],
      "recommendations": [
        "Implement proper secret management",
        "Sanitize logs to remove PII"
      ]
    },
    "documentation": {
      "api_documentation": "# PaymentProcessor Class\n\nSecure payment processing with webhook verification...",
      "security_notes": "## Security Considerations\n- Store API keys in Azure Key Vault\n- Use structured logging without PII",
      "usage_examples": [
        "processor = PaymentProcessor(api_key, webhook_secret)\nresult = await processor.process_payment(19.99, card_token)"
      ]
    },
    "testing_strategy": {
      "unit_tests": [
        "test_process_payment_success",
        "test_process_payment_invalid_amount",
        "test_webhook_verification"
      ],
      "mocks_required": ["PaymentClient", "logging"],
      "edge_cases": ["zero_amount", "negative_amount", "network_timeout"],
      "security_tests": ["webhook_signature_validation", "api_key_protection"]
    }
  },
  "agent_communication_log": [
    "code_reviewer → documentation_agent: security_findings",
    "testing_agent → code_reviewer: validation_request",
    "documentation_agent → all: context_incorporated"
  ],
  "guardrails_applied": ["output_length_check", "content_filter_passed"],
  "performance_metrics": {
    "total_duration_ms": 8500,
    "agent_execution_times": {
      "code_reviewer": 3200,
      "documentation_agent": 2800,
      "testing_agent": 2500
    }
  }
}
```

## 🚀 Deployment Options

### Option 1: Local Development Setup

1. **Configure local development:**
   ```json
   {
     "Values": {
       "MAX_AGENT_ITERATIONS": "3",
       "AGENT_TOKEN_LIMIT": "4000",
       "ENABLE_CONTENT_FILTER": "1",
       "MAX_CONCURRENT_AGENTS": "3"
     }
   }
   ```

2. **Benefits:**
   - Fast development iteration
   - Predictable mock responses
   - No AI service costs
   - Offline development capability

### Option 2: Cloud Deployment with Real AI Services

1. **Deploy with production AI capabilities:**
   ```bash
   azd up
   ```

2. **Production benefits:**
   - Real AI analysis and insights
   - Actual agent specialization
   - Production-scale performance
   - Complete observability

## 💡 Pro Tips from Your Mentor

### 🤝 Agent Coordination Best Practices:
- **Clear Protocols**: Define structured message formats for agent communication
- **State Management**: Use orchestrator context to track workflow progress
- **Conflict Resolution**: Implement precedence rules when agents disagree
- **Load Balancing**: Distribute work based on agent capabilities and availability

### 🛡️ Advanced Guardrails:
- **Token Budgets**: Limit per-agent output to prevent excessive costs
- **Content Filtering**: Block inappropriate or sensitive content
- **Loop Detection**: Prevent infinite agent communication cycles
- **Resource Limits**: Cap concurrent agent executions

### 📊 Performance Optimization:
- **Parallel Execution**: Run compatible agents simultaneously
- **Caching**: Reuse agent results for similar inputs
- **Circuit Breakers**: Protect against cascading failures
- **Monitoring**: Track agent performance and communication patterns

### 🔍 Debugging Multi-Agent Systems:
- **Correlation IDs**: Track messages across agent boundaries
- **Communication Logs**: Record all inter-agent messages
- **State Snapshots**: Capture workflow state at each iteration
- **Agent Traces**: Log individual agent decision processes

## 🎯 Success Indicators
You've mastered Level 6 when:
1. Multiple agents collaborate effectively on complex analysis tasks
2. Agent communication follows structured protocols with proper error handling
3. Guardrails prevent system abuse and maintain quality output
4. Workflow orchestration manages agent lifecycle and resource allocation
5. Results demonstrate value beyond what single agents could achieve
6. System handles agent failures without compromising overall workflow
7. You understand the trade-offs between agent specialization and generalization

**Ready for Level 7?** You'll implement enterprise-grade Zero Trust security!

---

## 📚 Additional Resources
- [Multi-Agent Systems in AI](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/concepts/multi-agent)
- [Azure Durable Functions Patterns](https://docs.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview)
- [Agent Communication Protocols](https://docs.microsoft.com/en-us/azure/architecture/patterns/messaging)
- [AI Safety and Guardrails](https://docs.microsoft.com/en-us/azure/cognitive-services/responsible-ai-overview)