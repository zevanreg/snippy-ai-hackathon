# =============================================================================
#
# This application demonstrates a modern AI-powered code snippet manager built with:
#
# 1. Azure Functions - Serverless compute that runs your code in the cloud
#    - HTTP triggers - Standard RESTful API endpoints accessible over HTTP
#    - MCP triggers - Model Context Protocol for AI agent integration (e.g., GitHub Copilot)
#
# 2. Azure Cosmos DB - NoSQL database with vector search capability
#    - Stores code snippets and their vector embeddings
#    - Enables semantic search through vector similarity
#
# 3. Azure OpenAI - Provides AI models and embeddings
#    - Generates vector embeddings from code snippets
#    - These embeddings capture the semantic meaning of the code
#
# 4. Azure AI Agents - Specialized AI agents for code analysis
#    - For generating documentation and style guides from snippets
#
# The application provides two parallel interfaces for the same functionality:
# - HTTP endpoints for traditional API access
# - MCP tools for AI assistant integration

import json
import logging
import azure.functions as func

app = func.FunctionApp()

# Register blueprints with enhanced error handling to prevent startup issues

# Core snippy functionality
try:
    from functions import bp_snippy
    app.register_blueprint(bp_snippy.bp)
    logging.info("✅ Snippy blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Snippy blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Snippy blueprint registration failed: {e}")

# Query functionality  
try:
    from routes import query
    app.register_blueprint(query.bp)
    logging.info("✅ Query blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Query blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Query blueprint registration failed: {e}")

# Embeddings functionality - now enabled for Level 2
try:
    from functions import bp_embeddings
    app.register_blueprint(bp_embeddings.bp)
    logging.info("✅ Embeddings blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Embeddings blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Embeddings blueprint registration failed: {e}")

# Ingestion functionality - blob trigger for Level 4
try:
    from functions import bp_ingestion
    app.register_blueprint(bp_ingestion.bp)
    logging.info("✅ Ingestion blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Ingestion blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Ingestion blueprint registration failed: {e}")

# Multi-agent functionality
try:
    from functions import bp_multi_agent
    app.register_blueprint(bp_multi_agent.bp)
    logging.info("✅ Multi-agent blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Multi-agent blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Multi-agent blueprint registration failed: {e}")


# =============================================================================
# HEALTH CHECK FUNCTIONALITY
# =============================================================================

# HTTP endpoint for health check
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def http_health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint to verify the service is running.
    
    Returns:
        JSON response with status "ok" and 200 status code
    """
    try:
        logging.info("Health check endpoint called")
        return func.HttpResponse(
            body=json.dumps({"status": "ok"}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in health check: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )


# HTTP endpoint for health check
@app.route(route="health_extended", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def http_health_check_extended(req: func.HttpRequest) -> func.HttpResponse:
    """
    Extended health check endpoint to verify service and dependencies are working.
    
    Returns:
        JSON response with detailed status information and appropriate status code
    """
    import os
    from datetime import datetime
    from azure.storage.blob.aio import BlobServiceClient
    from data.cosmos_ops import get_container
    
    logging.info("Extended health check endpoint called")
    
    health_status = {
        "status": "ok",
        "services": {
            "cosmos_db": {"status": "unknown"},
            "blob_storage": {"status": "unknown"}
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    overall_healthy = True
    
    # Check Cosmos DB connection
    try:
        container = await get_container()
        health_status["services"]["cosmos_db"] = {
            "status": "healthy",
            "database": os.environ.get("COSMOS_DATABASE_NAME"),
            "container": os.environ.get("COSMOS_CONTAINER_NAME")
        }
        logging.info("✅ Cosmos DB connection verified")
    except Exception as e:
        health_status["services"]["cosmos_db"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
        logging.error(f"❌ Cosmos DB connection failed: {str(e)}")
    
    # Check Blob Storage connection and INGESTION_CONTAINER
    try:
        ingestion_container = os.environ.get("INGESTION_CONTAINER", "snippet-inputs")
        storage_connection = os.environ.get("AzureWebJobsStorage")
        
        if not storage_connection:
            raise Exception("AzureWebJobsStorage connection string not configured")
        
        async with BlobServiceClient.from_connection_string(storage_connection) as blob_client:
            container_client = blob_client.get_container_client(ingestion_container)
            # Test if container exists by checking its properties
            await container_client.get_container_properties()
            
        health_status["services"]["blob_storage"] = {
            "status": "healthy",
            "ingestion_container": ingestion_container
        }
        logging.info(f"✅ Blob storage connection verified, container '{ingestion_container}' accessible")
    except Exception as e:
        health_status["services"]["blob_storage"] = {
            "status": "unhealthy",
            "error": str(e),
            "ingestion_container": os.environ.get("INGESTION_CONTAINER", "snippet-inputs")
        }
        overall_healthy = False
        logging.error(f"❌ Blob storage connection failed: {str(e)}")
    
    # Set overall status
    if not overall_healthy:
        health_status["status"] = "degraded"
    
    # Return appropriate status code
    status_code = 200 if overall_healthy else 503
    
    return func.HttpResponse(
        body=json.dumps(health_status, indent=2),
        mimetype="application/json",
        status_code=status_code
    )