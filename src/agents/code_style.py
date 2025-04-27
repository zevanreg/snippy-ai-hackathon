# Module for generating a code style guide using Azure AI Agents service.
# This module:
# - Defines the system prompt and instructions for the CodeStyleSynthesizer agent
# - Sets up Azure AI Project Client and authentication
# - Registers the vector_search tool for retrieving code examples
# - Manages the lifecycle of the AI agent, thread, messages, and run
# - Returns a comprehensive Markdown style guide based on code examples
import os
import logging
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AsyncFunctionTool
from azure.identity.aio import DefaultAzureCredential
from agents.tools import vector_search

# Configure logging for this module
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging to focus on our application logs
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure.ai.projects").setLevel(logging.WARNING)

# System prompt for the code style synthesizer agent
# This prompt defines the agent's personality, capabilities, and constraints
_CODE_STYLE_SYSTEM_PROMPT = """
You are CodeStyleSynthesizer, an autonomous agent that produces a code style guide.

You have access to a vector_search tool that can find relevant code snippets in the database.

Your task is to:
1. Perform a SINGLE vector search to find relevant code snippets that demonstrate various coding patterns
2. Analyze ALL patterns and conventions found in the code
3. Generate a comprehensive code style guide in Markdown format

The style guide should cover:
- Naming conventions
- Code organization
- Documentation standards
- Error handling
- Logging practices
- Any other relevant style aspects

For each section, provide:
- Clear, concise rules
- Examples from actual code snippets
- Best practices and recommendations

IMPORTANT: Use vector_search only ONCE to get a comprehensive set of examples. Do not make multiple searches.

Return only the final Markdown document, no additional commentary.
"""

async def generate_code_style() -> str:
    """
    Generates a code style guide using an AI agent.
    
    This function:
    1. Creates an AI agent with the CodeStyleSynthesizer personality
    2. Provides the agent with a vector search tool to find code examples
    3. Manages the agent's execution and tool calls
    4. Returns the generated style guide
    
    The agent uses Azure AI Agents service to:
    - Understand the task through the system prompt
    - Use the vector search tool to find relevant code
    - Generate a comprehensive style guide based on the code patterns
    
    Returns:
        str: The generated code style guide in Markdown format
    """
    try:
        # Log the system prompt for debugging and transparency
        logger.info("System prompt:\n%s", _CODE_STYLE_SYSTEM_PROMPT)
        
        # Create an Azure credential for authentication
        async with DefaultAzureCredential() as credential:
            # Connect to the Azure AI Project that hosts our agent
            async with AIProjectClient.from_connection_string(
                credential=credential,
                conn_str=os.environ["PROJECT_CONNECTION_STRING"]
            ) as project_client:
                # Create the vector search tool that the agent will use
                functions = AsyncFunctionTool(functions=[vector_search.vector_search])
                
                # Create the agent with its personality and tools
                agent = await project_client.agents.create_agent(
                    name="CodeStyleSynthesizer",
                    description="An agent that produces code style guides",
                    instructions=_CODE_STYLE_SYSTEM_PROMPT,
                    tools=functions.definitions,
                    model=os.environ["AGENTS_MODEL_DEPLOYMENT_NAME"]
                )
                logger.info("Created agent: %s with tool: vector_search", agent.name)
                
                # Create a conversation thread for the agent
                thread = await project_client.agents.create_thread()
                await project_client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content="Generate a code style guide."
                )
                
                # Start the agent's execution
                run = await project_client.agents.create_run(
                    thread_id=thread.id,
                    agent_id=agent.id
                )
                
                # Monitor the agent's progress and handle tool calls
                tool_call_count = 0
                while True:
                    run = await project_client.agents.get_run(thread_id=thread.id, run_id=run.id)
                    if run.status == "completed":
                        break
                    elif run.status == "failed":
                        raise Exception("Agent run failed")
                    elif run.status == "requires_action":
                        # Handle tool calls from the agent
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        tool_outputs = []
                        for tool_call in tool_calls:
                            logger.info("Agent %s calling tool: %s", agent.name, tool_call.function.name)
                            output = await functions.execute(tool_call)
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": output
                            })
                            tool_call_count += 1
                        await project_client.agents.submit_tool_outputs_to_run(
                            thread_id=thread.id,
                            run_id=run.id,
                            tool_outputs=tool_outputs
                        )
                
                # Get the final response from the agent
                messages = await project_client.agents.list_messages(thread_id=thread.id)
                response = str(messages.data[0].content[0].text.value)
                logger.info("Code style guide generated by %s (%d tool calls):\n%s", 
                          agent.name, tool_call_count, response)
                return response
                
    except Exception as e:
        logger.error("Code style generation failed: %s", str(e), exc_info=True)
        raise
