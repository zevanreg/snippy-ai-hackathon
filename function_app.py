import json
import logging
import azure.functions as func
import azure.durable_functions as df

from orchestrators import bp  # Import the blueprint
from activities import blob_ops, cosmos_ops
from agents import deep_research, code_style

app = func.FunctionApp()

# Register the Durable Functions blueprint
app.register_blueprint(bp)

# Constants for MCP tool properties
_SNIPPET_NAME_PROPERTY_NAME = "snippetname"
_SNIPPET_PROPERTY_NAME = "snippet"
_PROJECT_ID_PROPERTY_NAME = "projectid"
_BLOB_PATH = "snippets/{mcptoolargs." + _SNIPPET_NAME_PROPERTY_NAME + "}.json"

class ToolProperty:
    def __init__(self, property_name: str, property_type: str, description: str):
        self.propertyName = property_name
        self.propertyType = property_type
        self.description = description

    def to_dict(self):
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }

# Define the tool properties
tool_properties_save_snippets = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet."),
    ToolProperty(_PROJECT_ID_PROPERTY_NAME, "string", "The ID of the project."),
    ToolProperty(_SNIPPET_PROPERTY_NAME, "string", "The content of the snippet."),
]

tool_properties_get_snippets = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet."),
]

tool_properties_research = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet to research."),
]

tool_properties_code_style = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet to analyze."),
]

# Convert tool properties to JSON
tool_properties_save_snippets_json = json.dumps([prop.to_dict() for prop in tool_properties_save_snippets])
tool_properties_get_snippets_json = json.dumps([prop.to_dict() for prop in tool_properties_get_snippets])
tool_properties_research_json = json.dumps([prop.to_dict() for prop in tool_properties_research])
tool_properties_code_style_json = json.dumps([prop.to_dict() for prop in tool_properties_code_style])

# HTTP trigger for saving snippets
@app.route(route="snippets", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@app.durable_client_input(client_name="client")
async def http_save_snippet(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    """
    HTTP trigger function to save a code snippet.
    Starts the save_snippet_orchestrator to handle the fan-out/fan-in pattern.
    
    Args:
        req: The HTTP request
        client: The durable functions client
        
    Returns:
        HTTP response with status URL
    """
    try:
        req_body = req.get_json()
        
        required_fields = ["name", "projectId", "code"]
        for field in required_fields:
            if field not in req_body:
                return func.HttpResponse(
                    body=json.dumps({"error": f"Missing required field: {field}"}),
                    mimetype="application/json",
                    status_code=400
                )
        
        # Start the orchestration
        instance_id = await client.start_new(
            "save_snippet_orchestrator",
            None,
            client_input=req_body
        )
        
        logging.info(f"Started orchestration with ID = '{instance_id}'")
        
        response = client.create_check_status_response(req, instance_id)
        return response
    except Exception as e:
        logging.error(f"Error in http_save_snippet: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

# MCP tool trigger for saving snippets
@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="save_snippet",
    description="Save a code snippet with name and project ID.",
    toolProperties=tool_properties_save_snippets_json,
)
@app.durable_client_input(client_name="client")
async def mcp_save_snippet(context, client: df.DurableOrchestrationClient) -> str:
    """
    MCP tool trigger function to save a code snippet.
    
    Args:
        context: The MCP tool context (likely a JSON string)
        client: The durable functions client
        
    Returns:
        JSON string with operation result
    """
    try:
        # Parse the incoming context string
        mcp_data = json.loads(context)
        
        req_body = {
            "name": mcp_data["arguments"][_SNIPPET_NAME_PROPERTY_NAME],
            "projectId": mcp_data["arguments"][_PROJECT_ID_PROPERTY_NAME],
            "code": mcp_data["arguments"][_SNIPPET_PROPERTY_NAME]
        }
        
        # Start the orchestration
        instance_id = await client.start_new(
            "save_snippet_orchestrator",
            None,
            client_input=req_body
        )
        
        logging.info(f"Started orchestration with ID = '{instance_id}'")
        
        return json.dumps({
            "status": "started",
            "instanceId": instance_id
        })
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from MCP context: {context}")
        return json.dumps({"error": "Invalid JSON received in context"})
    except KeyError as e:
        logging.error(f"Missing key in parsed MCP context: {e}")
        return json.dumps({"error": f"Missing expected argument: {e}"})
    except Exception as e:
        logging.error(f"Error in mcp_save_snippet: {str(e)}")
        return json.dumps({"error": str(e)})

# HTTP trigger for getting snippets
@app.route(route="snippets/{name}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def http_get_snippet(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function to get a code snippet by name.
    
    Args:
        req: The HTTP request
        
    Returns:
        HTTP response with the snippet data
    """
    try:
        name = req.route_params.get("name")
        if not name:
            return func.HttpResponse(
                body=json.dumps({"error": "Missing snippet name in route"}),
                mimetype="application/json",
                status_code=400
            )
        
        # TODO: Fix storage account authentication before implementing
        logging.info(f"HTTP - Getting snippet with name {name}")
        return func.HttpResponse(
            body=json.dumps({
                "id": name,
                "projectId": "test-project",
                "code": "def hello_world():\n    print('Hello, World!')",
                "blobUrl": "dummy-blob-url",
                "embedding": [0.0] * 1536
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in http_get_snippet: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

# MCP tool trigger for getting snippets
@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_snippet",
    description="Get a code snippet by name.",
    toolProperties=tool_properties_get_snippets_json,
)
async def mcp_get_snippet(context) -> str:
    """
    MCP tool trigger function to get a code snippet by name.
    
    Args:
        context: The MCP tool context (likely a JSON string)
        
    Returns:
        JSON string with the snippet data
    """
    try:
        # Parse the incoming context string
        mcp_data = json.loads(context)
        
        name = mcp_data["arguments"][_SNIPPET_NAME_PROPERTY_NAME]
        if not name:
            return json.dumps({"error": "Missing snippet name in MCP context"})
        
        # TODO: Fix storage account authentication before implementing
        logging.info(f"MCP - Getting snippet with name {name}")
        return json.dumps({
            "id": name,
            "projectId": "test-project",
            "code": "def hello_world():\n    print('Hello, World!')",
            "blobUrl": "dummy-blob-url",
            "embedding": [0.0] * 1536
        })
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from MCP context: {context}")
        return json.dumps({"error": "Invalid JSON received in context"})
    except KeyError as e:
        logging.error(f"Missing key in parsed MCP context: {e}")
        return json.dumps({"error": f"Missing expected argument: {e}"})
    except Exception as e:
        logging.error(f"Error in mcp_get_snippet: {str(e)}")
        return json.dumps({"error": str(e)})

# HTTP trigger for deep research
@app.route(route="snippets/{name}/research", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def http_deep_research(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function to perform deep research on a code snippet.
    
    Args:
        req: The HTTP request
        
    Returns:
        HTTP response with the research results
    """
    try:
        name = req.route_params.get("name")
        if not name:
            return func.HttpResponse(
                body=json.dumps({"error": "Missing snippet name in route"}),
                mimetype="application/json",
                status_code=400
            )
        
        # TODO: Fix storage account authentication before implementing
        logging.info(f"HTTP - Would perform research on snippet {name}")
        return func.HttpResponse(
            body=json.dumps({
                "research": "Dummy research results for snippet " + name
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in http_deep_research: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

# MCP tool trigger for deep research
@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="deep_research",
    description="Perform deep research on a code snippet.",
    toolProperties=tool_properties_research_json,
)
async def mcp_deep_research(context) -> str:
    """
    MCP tool trigger function to perform deep research on a code snippet.
    
    Args:
        context: The MCP tool context (likely a JSON string)
        
    Returns:
        JSON string with the research results
    """
    try:
        # Parse the incoming context string
        mcp_data = json.loads(context)
        
        name = mcp_data["arguments"][_SNIPPET_NAME_PROPERTY_NAME]
        if not name:
            return json.dumps({"error": "Missing snippet name in MCP context"})
        
        # TODO: Fix storage account authentication before implementing
        logging.info(f"MCP - Would perform research on snippet {name}")
        return json.dumps({
            "research": "Dummy research results for snippet " + name
        })
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from MCP context: {context}")
        return json.dumps({"error": "Invalid JSON received in context"})
    except KeyError as e:
        logging.error(f"Missing key in parsed MCP context: {e}")
        return json.dumps({"error": f"Missing expected argument: {e}"})
    except Exception as e:
        logging.error(f"Error in mcp_deep_research: {str(e)}")
        return json.dumps({"error": str(e)})

# HTTP trigger for code style
@app.route(route="snippets/{name}/code-style", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def http_code_style(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function to generate a code style guide based on a snippet.
    
    Args:
        req: The HTTP request
        
    Returns:
        HTTP response with the code style guide
    """
    try:
        name = req.route_params.get("name")
        if not name:
            return func.HttpResponse(
                body=json.dumps({"error": "Missing snippet name in route"}),
                mimetype="application/json",
                status_code=400
            )
        
        # TODO: Fix storage account authentication before implementing
        logging.info(f"HTTP - Would generate code style for snippet {name}")
        return func.HttpResponse(
            body=json.dumps({
                "styleGuide": "Dummy style guide for snippet " + name
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in http_code_style: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

# MCP tool trigger for code style
@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="code_style",
    description="Generate a code style guide based on a snippet.",
    toolProperties=tool_properties_code_style_json,
)
async def mcp_code_style(context) -> str:
    """
    MCP tool trigger function to generate a code style guide based on a snippet.
    
    Args:
        context: The MCP tool context (likely a JSON string)
        
    Returns:
        JSON string with the code style guide
    """
    try:
        # Parse the incoming context string
        mcp_data = json.loads(context)
        
        name = mcp_data["arguments"][_SNIPPET_NAME_PROPERTY_NAME]
        if not name:
            return json.dumps({"error": "Missing snippet name in MCP context"})
        
        # TODO: Fix storage account authentication before implementing
        logging.info(f"MCP - Would generate code style for snippet {name}")
        return json.dumps({
            "styleGuide": "Dummy style guide for snippet " + name
        })
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from MCP context: {context}")
        return json.dumps({"error": "Invalid JSON received in context"})
    except KeyError as e:
        logging.error(f"Missing key in parsed MCP context: {e}")
        return json.dumps({"error": f"Missing expected argument: {e}"})
    except Exception as e:
        logging.error(f"Error in mcp_code_style: {str(e)}")
        return json.dumps({"error": str(e)})

@bp.activity_trigger(input_name="payload")
def upload_raw_code_activity(payload: dict) -> str:
    """
    Activity function to upload raw code to blob storage.
    TODO: Fix storage account authentication before implementing
    
    Args:
        payload: The payload containing code, project_id, and name
        
    Returns:
        The URL of the uploaded blob
    """
    # TODO: Implement proper blob storage upload once authentication is fixed
    logging.info(f"Would upload code with length {len(payload['code'])} to blob storage")
    return "dummy-blob-url"

@bp.activity_trigger(input_name="code")
def generate_embedding_activity(code: str) -> list:
    """
    Activity function to generate an embedding for code.
    TODO: Implement proper embeddings generation once binding is fixed
    
    Args:
        code: The code content to generate an embedding for
        
    Returns:
        The embedding vector
    """
    logging.info(f"Generating embedding for code with length {len(code)}")
    # TODO: Replace with proper embeddings generation
    # For now, return a dummy embedding
    return [0.0] * 1536  # Standard embedding size

@bp.activity_trigger(input_name="payload")
def upsert_document_activity(payload: dict) -> dict:
    """
    Activity function to upsert a document to Cosmos DB.
    TODO: Fix storage account authentication before implementing
    
    Args:
        payload: The payload containing name, project_id, code, blob_url, and embedding
        
    Returns:
        The created/updated document
    """
    # TODO: Implement proper Cosmos DB upsert once authentication is fixed
    logging.info(f"Would upsert document with name {payload['name']} to Cosmos DB")
    return {
        "id": payload["name"],
        "projectId": payload["project_id"],
        "code": payload["code"],
        "blobUrl": payload["blob_url"],
        "embedding": payload["embedding"]
    }
