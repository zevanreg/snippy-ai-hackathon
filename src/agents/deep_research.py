# Module for performing deep research analysis on code snippets using Azure AI Agents.
# This module:
# - Sets up Azure AI Project Client and authentication
# - Creates an agent to analyze code semantics, patterns, and best practices
# - Sends user messages and polls for agent run completion
# - Returns detailed research findings
import os
import logging
import time
import json
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageTextContent
from azure.identity import DefaultAzureCredential

async def perform_deep_research(snippet_text: str, similar_snippets: list) -> str:
    """
    Performs deep research on a code snippet using Azure AI Projects.
    
    Args:
        snippet_text: The text of the snippet to research
        similar_snippets: List of similar snippets from vector search
        
    Returns:
        The research results as a string
    """
    try:
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        
        context = f"Main code snippet:\n```\n{snippet_text}\n```\n\n"
        
        if similar_snippets and len(similar_snippets) > 0:
            context += "Similar snippets found in the repository:\n"
            for i, similar in enumerate(similar_snippets):
                context += f"\nSimilar snippet {i+1} (ID: {similar['id']}):\n```\n{similar['code']}\n```\n"
        
        agent = project_client.agents.create_agent(
            name="DeepResearchAgent",
            description="An agent that performs deep research on code snippets",
            instructions="""
            Perform a deep research analysis on the provided code snippet. Your analysis should include:
            
            1. A detailed explanation of what the code does
            2. Identification of any patterns, algorithms, or design principles used
            3. Potential optimizations or improvements
            4. Security considerations
            5. Best practices that are followed or could be followed
            6. Similar code patterns found in the repository and how they relate
            
            Provide a comprehensive analysis that would help a developer understand and improve this code.
            """
        )
        
        thread = project_client.agents.create_thread()
        
        project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=MessageTextContent(text=context)
        )
        
        run = project_client.agents.create_run(
            thread_id=thread.id,
            agent_id=agent.id
        )
        
        while True:
            run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)
            if run.status == "completed":
                break
            elif run.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Run failed with status: {run.status}")
            time.sleep(1)
        
        messages = project_client.agents.list_messages(thread_id=thread.id)
        
        assistant_messages = [msg for msg in messages if msg.role == "assistant"]
        if not assistant_messages:
            raise Exception("No assistant messages found")
        
        last_message = assistant_messages[-1]
        return last_message.content[0].text
    except Exception as e:
        logging.error(f"Error performing deep research: {str(e)}")
        raise
