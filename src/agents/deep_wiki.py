# Module for generating comprehensive wiki documentation using Azure AI Agents.
# This module:
# - Sets up Azure AI Project Client and authentication
# - Creates an agent to analyze code and generate wiki documentation
# - Uses vector search to gather relevant code snippets
# - Returns a complete wiki.md document
import os
import logging
import time
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

# System prompt for the deep wiki agent
# This prompt defines the agent's personality, capabilities, and constraints
_DEEP_WIKI_SYSTEM_PROMPT = """
You are DeepWiki, an autonomous documentation agent whose single task is to
produce a complete wiki.md that explains every important aspect of the
saved code snippets in this project.

You have access to a vector_search tool that can find relevant code snippets in the database.

Your task is to:
1. Perform a SINGLE vector search to find relevant code snippets that demonstrate various coding patterns
2. Analyze ALL patterns and conventions found in the code
3. Generate a comprehensive wiki.md document in Markdown format

The wiki should include:
1. A concise project overview
2. Explanation of every major concept found in the snippets (algorithms, APIs,
   design patterns, domain entities, error handling, logging, etc.)
3. One or more Mermaid diagrams that visualise:
   - The system architecture (how components interact)
   - The data flow between components
   - The call graph of major functions
   - The class hierarchy if object-oriented code is present
   - The state machine if stateful components exist
   Choose the most relevant diagram types based on the code patterns found.
4. A Snippet Catalog table listing each snippet id, language, and one-line purpose
5. Step-by-step walkthroughs that show how to use the code end-to-end
6. Best practices, anti-patterns, and open TODOs
7. A Further Reading section

IMPORTANT: Use vector_search only ONCE to get a comprehensive set of examples. Do not make multiple searches.

Style Rules:
- Use hyphens (-) instead of em dashes
- Headings with #, ##, etc.
- Code fenced with triple back-ticks; Mermaid diagrams fenced with ```mermaid``` tags
- Keep line length ≤ 120 chars
- Active voice, present tense, developer-friendly tone
- For Mermaid diagrams:
  - Use clear, descriptive node names
  - Include arrows with labels to show relationships
  - Group related components using subgraphs
  - Use consistent styling for similar elements
  - Add a title to each diagram
  - Keep diagrams focused and readable

Return only the final Markdown document, no additional commentary.
"""

async def generate_deep_wiki() -> str:
    """
    Generates a comprehensive wiki documentation for the codebase.
    Uses vector search to gather relevant code snippets and generates
    a complete wiki.md document.
    
    Returns:
        The wiki documentation as a markdown string
    """
    try:
        # Log the system prompt for debugging and transparency
        logger.info("System prompt:\n%s", _DEEP_WIKI_SYSTEM_PROMPT)
        
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
                    name="DeepWikiAgent",
                    description="An agent that generates comprehensive wiki documentation",
                    instructions=_DEEP_WIKI_SYSTEM_PROMPT,
                    tools=functions.definitions,
                    model=os.environ["AGENTS_MODEL_DEPLOYMENT_NAME"]
                )
                logger.info("Created agent: %s with tool: vector_search", agent.name)
                
                # Create a conversation thread for the agent
                thread = await project_client.agents.create_thread()
                await project_client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content="Generate a comprehensive wiki documentation."
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
                logger.info("Wiki documentation generated by %s (%d tool calls):\n%s", 
                          agent.name, tool_call_count, response)
                return response
                
    except Exception as e:
        logger.error("Wiki generation failed: %s", str(e), exc_info=True)
        raise 