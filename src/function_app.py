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