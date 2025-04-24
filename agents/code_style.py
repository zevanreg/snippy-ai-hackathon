import os
import logging
import time
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageTextContent
from azure.identity import DefaultAzureCredential

async def generate_code_style(snippet_text: str, similar_snippets: list) -> str:
    """
    Generates a code style guide based on a snippet and similar snippets.
    
    Args:
        snippet_text: The text of the snippet to analyze
        similar_snippets: List of similar snippets from vector search
        
    Returns:
        The generated code style guide as a string
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
            name="CodeStyleAgent",
            description="An agent that analyzes code and creates style guides",
            instructions="""
            You are a code style expert that analyzes code and creates style guides.
            Generate a reusable code-style guide based on the provided code snippets.
            The style guide should cover:
            
            1. Naming conventions for variables, functions, classes, etc.
            2. Formatting rules (indentation, line length, etc.)
            3. Comment style and documentation practices
            4. Error handling patterns
            5. Design patterns and architectural approaches
            6. Testing conventions
            
            The guide should be specific to the language and frameworks used in the snippets
            and should be consistent with the existing code style.
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
        logging.error(f"Error generating code style: {str(e)}")
        raise
