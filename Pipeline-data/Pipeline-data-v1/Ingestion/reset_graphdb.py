"""
Script: Reset GraphDB Repository
Clears all triples from GraphDB repository.
"""

import os
import logging
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load environment variables from root .env
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def reset_graphdb():
    """Delete all triples from GraphDB repository."""
    graphdb_url = os.getenv('GRAPHDB_URL')
    graphdb_repo = os.getenv('GRAPHDB_REPOSITORY')
    graphdb_username = os.getenv('GRAPHDB_USERNAME')
    graphdb_password = os.getenv('GRAPHDB_PASSWORD')
    
    endpoint = f"{graphdb_url}/repositories/{graphdb_repo}/statements"
    
    auth = None
    if graphdb_username and graphdb_password:
        auth = (graphdb_username, graphdb_password)
    
    logger.info(f"Connecting to GraphDB: {graphdb_url}")
    logger.info(f"Repository: {graphdb_repo}")
    
    try:
        # Try DELETE request first (REST API method)
        response = requests.delete(
            endpoint,
            auth=auth,
            timeout=30
        )
        
        if response.status_code in [200, 204]:
            logger.info(f"✅ GraphDB repository cleared successfully via DELETE (status: {response.status_code})")
            return True
        else:
            logger.warning(f"DELETE endpoint returned {response.status_code}, trying SPARQL UPDATE...")
            
            # Fallback to SPARQL UPDATE
            sparql_query = "DELETE WHERE { ?s ?p ?o }"
            
            headers = {
                'Content-Type': 'application/sparql-update'
            }
            
            response = requests.post(
                endpoint,
                data=sparql_query.encode('utf-8'),
                headers=headers,
                auth=auth,
                timeout=30
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"✅ GraphDB repository cleared successfully via SPARQL (status: {response.status_code})")
                return True
            else:
                logger.error(f"❌ Failed to clear repository (status: {response.status_code}): {response.text}")
                return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error: {e}")
        return False


def get_triple_count():
    """Get current triple count from GraphDB repository (default graph + named graphs)."""
    graphdb_url = os.getenv('GRAPHDB_URL')
    graphdb_repo = os.getenv('GRAPHDB_REPOSITORY')
    graphdb_username = os.getenv('GRAPHDB_USERNAME')
    graphdb_password = os.getenv('GRAPHDB_PASSWORD')
    
    # Use query endpoint specific to this repository
    query_endpoint = f"{graphdb_url}/repositories/{graphdb_repo}"
    
    auth = None
    if graphdb_username and graphdb_password:
        auth = (graphdb_username, graphdb_password)
    
    # Count triples in both default graph and named graphs
    sparql_query = """SELECT (COUNT(*) as ?count) WHERE { 
        { ?s ?p ?o } 
        UNION 
        { GRAPH ?g { ?s ?p ?o } } 
    }"""
    
    try:
        response = requests.post(
            query_endpoint,
            data={'query': sparql_query},
            headers={'Accept': 'application/sparql-results+json'},
            auth=auth,
            timeout=10
        )
        
        if response.status_code == 200:
            results = response.json()
            bindings = results.get('results', {}).get('bindings', [])
            if bindings:
                count = bindings[0].get('count', {}).get('value', 0)
                return int(count)
        
        return 0
    except Exception as e:
        logger.error(f"Error getting triple count: {e}")
        return -1


def main():
    """Main reset pipeline."""
    logger.info(f"\n{'='*50}")
    logger.info("GraphDB Repository Reset")
    logger.info(f"{'='*50}\n")
    
    # Get current count
    initial_count = get_triple_count()
    if initial_count >= 0:
        logger.info(f"Current triples in GraphDB: {initial_count}")
    
    # Reset repository
    if reset_graphdb():
        # Wait for GraphDB to process the deletion
        logger.info("Waiting 2 seconds for GraphDB to process deletion...")
        time.sleep(2)
        
        # Verify
        final_count = get_triple_count()
        if final_count >= 0:
            logger.info(f"Triples after reset: {final_count}")
            if final_count == 0:
                logger.info(f"\n✅ GraphDB repository is now clean!")
            else:
                logger.warning(f"\n⚠️  Some triples remain: {final_count}")
    else:
        logger.error("\n❌ Reset failed")


if __name__ == '__main__':
    main()
