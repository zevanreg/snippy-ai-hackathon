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
        project_id = payload.get("projectId", "default-project")
        code = payload["code"]
        
        logging.info(f"Starting orchestration for snippet {name} in project {project_id}")
        logging.info(f"Input payload: {payload}")
        
        # Schedule activity calls in parallel
        logging.info("Scheduling parallel activities: upload_raw_code_activity and generate_embedding_activity")
        upload = context.call_activity("upload_raw_code_activity", {
            "code": code,
            "project_id": project_id,
            "name": name
        })
        embed = context.call_activity("generate_embedding_activity", code)
        
        # Wait for all activities to complete
        logging.info("Waiting for parallel activities to complete...")
        blob_url, embedding = yield context.task_all([upload, embed])
        logging.info(f"Activities completed. Blob URL: {blob_url}, Embedding length: {len(embedding) if embedding else 0}")
        
        # Prepare document for upsert
        upsert_payload = {
            "name": name,
            "project_id": project_id,
            "code": code,
            "blob_url": blob_url,
            "embedding": embedding
        }
        logging.info(f"Preparing to upsert document with payload: {upsert_payload}")
        
        # Upsert the document
        logging.info("Calling upsert_document_activity...")
        result = yield context.call_activity("upsert_document_activity", upsert_payload)
        logging.info(f"Upsert completed with result: {result}")
        
        return {
            "id": result["id"],
            "projectId": result["projectId"],
            "status": "completed"
        }
    except Exception as e:
        logging.error(f"Error in orchestrator: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        logging.error(f"Error details: {str(e)}")
        raise
