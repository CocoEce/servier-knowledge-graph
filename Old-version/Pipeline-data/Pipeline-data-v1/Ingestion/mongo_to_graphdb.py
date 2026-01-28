"""
Script: MongoDB to GraphDB Synchronization
Reads triples from MongoDB and syncs them to GraphDB via SPARQL Update.
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path

import requests
from pymongo import MongoClient
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables from root .env
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(env_path)

MONGO_DATABASE = 'Servier'
MONGO_COLLECTION = 'GraphDB'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MongoToGraphDBSync:
    """Synchronize triples from MongoDB to GraphDB."""
    
    def __init__(self):
        """Initialize MongoDB and GraphDB connections."""
        # MongoDB setup
        self.mongo_uri = os.getenv('MONGODB_URI')
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client[MONGO_DATABASE]
        self.collection = self.db[MONGO_COLLECTION]
        
        # GraphDB setup
        self.graphdb_url = os.getenv('GRAPHDB_URL')
        self.graphdb_repo = os.getenv('GRAPHDB_REPOSITORY')
        self.graphdb_username = os.getenv('GRAPHDB_USERNAME')
        self.graphdb_password = os.getenv('GRAPHDB_PASSWORD')
        
        # GraphDB has two endpoints: /statements (application/x-ntriples) and /rdf-graphs/service (SPARQL Update)
        self.graphdb_statements_endpoint = f"{self.graphdb_url}/repositories/{self.graphdb_repo}/statements"
        self.graphdb_update_endpoint = f"{self.graphdb_url}/repositories/{self.graphdb_repo}/statements"
        
        # Auth if credentials provided
        self.auth = None
        if self.graphdb_username and self.graphdb_password:
            self.auth = (self.graphdb_username, self.graphdb_password)
        
        logger.info(f"MongoDB connected: {self.mongo_uri[:50]}...")
        logger.info(f"GraphDB endpoint: {self.graphdb_update_endpoint}")
        logger.info(f"GraphDB repository: {self.graphdb_repo}")
    
    def escape_rdf_value(self, value: str, is_uri: bool = False, datatype: str = None, language: str = None) -> str:
        """
        Escape RDF values for N-Triples format.
        
        Args:
            value: The value to escape
            is_uri: Whether this is a URI (True) or literal (False)
            datatype: Optional XSD datatype for literals (e.g., "http://www.w3.org/2001/XMLSchema#integer")
            language: Optional language tag for literals (e.g., "en")
            
        Returns:
            Escaped RDF value in N-Triples format
        """
        if is_uri:
            # URIs must be wrapped in angle brackets
            return f"<{value}>"
        else:
            # Escape special characters in literals first
            value = value.replace('\\', '\\\\')
            value = value.replace('"', '\\"')
            value = value.replace('\n', '\\n')
            value = value.replace('\r', '\\r')
            value = value.replace('\t', '\\t')
            
            # Build literal with optional language tag or datatype
            if language:
                return f'"{value}"@{language}'
            elif datatype:
                return f'"{value}"^^<{datatype}>'
            else:
                return f'"{value}"'
    
    def triple_to_ntriples(self, triple: Dict[str, Any]) -> str:
        """
        Convert a triple dictionary to N-Triples format.
        Preserves RDF type information (URIs, typed literals, language tags).
        
        Args:
            triple: Dictionary with 'subject', 'predicate', 'object', 'object_type',
                    'object_datatype' (optional), 'object_language' (optional)
            
        Returns:
            N-Triples format string
        """
        # Subject is always a URI
        subject = self.escape_rdf_value(triple['subject'], is_uri=True)
        # Predicate is always a URI
        predicate = self.escape_rdf_value(triple['predicate'], is_uri=True)
        
        # Check if object is URI or literal
        is_uri = triple.get('object_type') == 'uri'
        datatype = triple.get('object_datatype') if not is_uri else None
        language = triple.get('object_language') if not is_uri else None
        
        obj = self.escape_rdf_value(triple['object'], is_uri=is_uri, datatype=datatype, language=language)
        
        return f"{subject} {predicate} {obj} ."
    
    def fetch_triples_from_mongo(self, batch_size: int = 1000, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch triples from MongoDB.
        
        Args:
            batch_size: Number of triples per batch
            skip: Number of triples to skip
            
        Returns:
            List of triple dictionaries
        """
        try:
            triples = list(
                self.collection.find({})
                .skip(skip)
                .limit(batch_size)
            )
            logger.info(f"Fetched {len(triples)} triples from MongoDB (skip={skip})")
            return triples
        except Exception as e:
            logger.error(f"Error fetching triples from MongoDB: {e}")
            return []
    
    def send_to_graphdb(self, ntriples: str) -> bool:
        """
        Send N-Triples data to GraphDB via SPARQL UPDATE.
        
        Args:
            ntriples: N-Triples format string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert N-Triples to SPARQL INSERT format
            sparql_query = self._ntriples_to_sparql_insert(ntriples)
            
            headers = {
                'Content-Type': 'application/sparql-update'
            }
            
            response = requests.post(
                self.graphdb_update_endpoint,
                data=sparql_query.encode('utf-8'),
                headers=headers,
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code in [200, 201, 204]:
                logger.info(f"Successfully sent data to GraphDB (status: {response.status_code})")
                return True
            else:
                logger.error(f"GraphDB error ({response.status_code}): {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error sending to GraphDB: {e}")
            return False
    
    def _ntriples_to_sparql_insert(self, ntriples: str) -> str:
        """Convert N-Triples to SPARQL INSERT query."""
        return f"INSERT DATA {{\n{ntriples}\n}}"
    
    def get_graphdb_stats(self) -> Dict[str, Any]:
        """Get statistics from GraphDB."""
        try:
            # Use SPARQL query to get triple count (only named graphs)
            sparql_query = "SELECT (COUNT(*) as ?count) WHERE { GRAPH ?g { ?s ?p ?o } }"
            
            query_endpoint = f"{self.graphdb_url}/repositories/{self.graphdb_repo}"
            response = requests.post(
                query_endpoint,
                data={'query': sparql_query},
                headers={'Accept': 'application/sparql-results+json'},
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                bindings = results.get('results', {}).get('bindings', [])
                if bindings:
                    count = bindings[0].get('count', {}).get('value', 'N/A')
                    return {'total_triples': count}
            
            return {}
        except Exception as e:
            logger.warning(f"Could not fetch GraphDB stats: {e}")
            return {}
    
    def sync(self, batch_size: int = 1000, max_batches: int = None) -> int:
        """
        Synchronize all triples from MongoDB to GraphDB.
        
        Args:
            batch_size: Number of triples per batch
            max_batches: Maximum number of batches to process (None = all)
            
        Returns:
            Total number of triples synced
        """
        total_synced = 0
        batch_count = 0
        skip = 0
        
        while True:
            if max_batches and batch_count >= max_batches:
                logger.info(f"Reached max batches limit ({max_batches})")
                break
            
            # Fetch batch from MongoDB
            triples = self.fetch_triples_from_mongo(batch_size=batch_size, skip=skip)
            
            if not triples:
                logger.info("No more triples to fetch from MongoDB")
                break
            
            # Convert to N-Triples format
            ntriples_list = [self.triple_to_ntriples(triple) for triple in triples]
            ntriples_data = '\n'.join(ntriples_list)
            
            logger.info(f"Batch {batch_count + 1}: Sending {len(ntriples_list)} triples to GraphDB")
            
            # Send to GraphDB
            if self.send_to_graphdb(ntriples_data):
                total_synced += len(ntriples_list)
                logger.info(f"Total synced so far: {total_synced}")
            else:
                logger.warning(f"Batch {batch_count + 1} failed, continuing...")
            
            batch_count += 1
            skip += batch_size
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Synchronization Complete!")
        logger.info(f"Total triples synced: {total_synced}")
        
        return total_synced
    
    def close(self):
        """Close MongoDB connection."""
        self.mongo_client.close()
        logger.info("MongoDB connection closed")


def main():
    """Main synchronization pipeline."""
    sync = MongoToGraphDBSync()
    
    try:
        # Perform sync
        total_synced = sync.sync(batch_size=1000)
        
        # Display GraphDB stats
        stats = sync.get_graphdb_stats()
        if stats:
            logger.info(f"GraphDB statistics:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
        
    finally:
        sync.close()


if __name__ == '__main__':
    main()
