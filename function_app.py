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

@app.route(route="snippets", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@app.durable_client_input(client_name="client")
async def save_snippet(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
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
        # In Python v2 programming model, get_json() is synchronous
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
            "save_snippet_orchestrator",  # orchestration_function_name
            None,                         # instance_id (let DF pick one)
            client_input=req_body         # payload sent to orchestrator
        )
        
        logging.info(f"Started orchestration with ID = '{instance_id}'")
        
        # Create the status response - synchronous in v2
        response = client.create_check_status_response(req, instance_id)
        return response
    except Exception as e:
        logging.error(f"Error in save_snippet: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="snippets/{name}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def get_snippet(req: func.HttpRequest) -> func.HttpResponse:
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
        logging.info(f"Would get snippet with name {name}")
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
        logging.error(f"Error in get_snippet: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="snippets/{name}/research", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def deep_research_function(req: func.HttpRequest) -> func.HttpResponse:
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
        logging.info(f"Would perform research on snippet {name}")
        return func.HttpResponse(
            body=json.dumps({
                "research": "Dummy research results for snippet " + name
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in deep_research: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="snippets/{name}/code-style", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def create_code_style_function(req: func.HttpRequest) -> func.HttpResponse:
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
        logging.info(f"Would generate code style for snippet {name}")
        return func.HttpResponse(
            body=json.dumps({
                "styleGuide": "Dummy style guide for snippet " + name
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in create_code_style: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

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
