import logging
import azure.durable_functions as df

# Create a Durable Functions blueprint
bp = df.Blueprint()

@bp.orchestration_trigger(context_name="context")
def save_snippet_orchestrator(context: df.DurableOrchestrationContext):
    """
    Orchestrator function for saving a snippet with fan-out/fan-in pattern.
    
    Args:
        context: The orchestration context
        
    Returns:
        The result of the orchestration
    """
    try:
        payload = context.get_input()
        name = payload["name"]
        project_id = payload["projectId"]
        code = payload["code"]
        
        logging.info(f"Starting orchestration for snippet {name} in project {project_id}")
        
        # Schedule activity calls in parallel
        upload = context.call_activity("upload_raw_code", {
            "code": code,
            "project_id": project_id,
            "name": name
        })
        embed = context.call_activity("generate_embedding", code)
        
        # Wait for all activities to complete
        blob_url, embedding = yield context.task_all([upload, embed])
        
        # Upsert the document
        result = yield context.call_activity("upsert_document", {
            "name": name,
            "project_id": project_id,
            "code": code,
            "blob_url": blob_url,
            "embedding": embedding
        })
        
        return {
            "id": result["id"],
            "projectId": result["projectId"],
            "status": "completed"
        }
    except Exception as e:
        logging.error(f"Error in orchestrator: {str(e)}")
        raise
