"""
Script: TTL to MongoDB Ingestion
Converts RDF Turtle files to JSON and stores in MongoDB Atlas.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import logging
import sys

from rdflib import Graph
from pymongo import MongoClient, errors
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


class TTLToMongoIngestion:
    """Convert TTL files to JSON and ingest into MongoDB."""
    
    def __init__(self):
        """Initialize MongoDB connection and RDF graph."""
        self.mongo_uri = os.getenv('MONGODB_URI')
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client[MONGO_DATABASE]
        self.collection = self.db[MONGO_COLLECTION]
        
        # Create index on subject, predicate for faster queries
        self.collection.create_index([('subject', 1), ('predicate', 1)])
        
        logger.info("MongoDB connection established")
    
    def ttl_to_triples(self, ttl_file: str) -> List[Dict[str, Any]]:
        """
        Parse TTL file and convert to list of triples.
        
        Args:
            ttl_file: Path to TTL file
            
        Returns:
            List of dictionaries with subject, predicate, object
        """
        triples = []
        
        try:
            graph = Graph()
            graph.parse(ttl_file, format='turtle')
            
            for subject, predicate, obj in graph:
                triple = {
                    'source_file': Path(ttl_file).name,
                    'subject': str(subject),
                    'predicate': str(predicate),
                    'object': str(obj),
                    'subject_type': self._get_node_type(subject),
                    'object_type': self._get_node_type(obj),
                }
                triples.append(triple)
            
            logger.info(f"Parsed {len(triples)} triples from {ttl_file}")
            return triples
            
        except Exception as e:
            logger.error(f"Error parsing {ttl_file}: {e}")
            return []
    
    def _get_node_type(self, node) -> str:
        """Determine if node is URI, Literal, or Blank."""
        if isinstance(node, str):
            return 'literal'
        elif hasattr(node, 'startswith'):  # URI
            return 'uri'
        else:
            return 'blank'
    
    def ingest_triples(self, triples: List[Dict[str, Any]]) -> int:
        """
        Insert or replace triples in MongoDB (no duplicates).
        
        Args:
            triples: List of triple dictionaries
            
        Returns:
            Number of triples inserted/replaced
        """
        if not triples:
            return 0
        
        try:
            count = 0
            for triple in triples:
                # Use subject + predicate + object as unique key
                filter_query = {
                    'subject': triple['subject'],
                    'predicate': triple['predicate'],
                    'object': triple['object']
                }
                
                # Replace if exists, insert if not
                result = self.collection.replace_one(
                    filter_query,
                    triple,
                    upsert=True
                )
                
                # Count new inserts (not replacements)
                if result.upserted_id is not None or result.modified_count > 0:
                    count += 1
            
            logger.info(f"Inserted/replaced {count} triples into MongoDB")
            return count
            
        except Exception as e:
            logger.error(f"Error inserting triples: {e}")
            return 0
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        count = self.collection.count_documents({})
        subjects = self.collection.distinct('subject')
        predicates = self.collection.distinct('predicate')
        
        return {
            'total_triples': count,
            'unique_subjects': len(subjects),
            'unique_predicates': len(predicates),
            'source_files': self.collection.distinct('source_file')
        }
    
    def clear_collection(self):
        """Clear all data from collection (use with caution)."""
        result = self.collection.delete_many({})
        logger.warning(f"Deleted {result.deleted_count} documents from collection")
    
    def close(self):
        """Close MongoDB connection."""
        self.mongo_client.close()
        logger.info("MongoDB connection closed")


def main():
    """Main ingestion pipeline."""
    ingestion = TTLToMongoIngestion()
    
    try:
        # Get all TTL files in Sources directory
        sources_dir = Path(__file__).resolve().parents[1] / 'Sources'
        ttl_files = list(sources_dir.glob('*.ttl'))
        
        if not ttl_files:
            logger.error(f"No TTL files found in {sources_dir}")
            logger.info(f"Looking for .ttl files in: {sources_dir}")
            return
        
        logger.info(f"Found {len(ttl_files)} TTL files in {sources_dir}")
        
        total_inserted = 0
        
        # Process each TTL file
        for ttl_file in sorted(ttl_files):
            logger.info(f"\nProcessing: {ttl_file}")
            
            # Parse TTL to triples
            triples = ingestion.ttl_to_triples(str(ttl_file))
            
            if triples:
                # Ingest into MongoDB
                inserted = ingestion.ingest_triples(triples)
                total_inserted += inserted
        
        # Display statistics
        stats = ingestion.get_collection_stats()
        logger.info(f"\n{'='*50}")
        logger.info(f"Ingestion Complete!")
        logger.info(f"Total triples inserted: {total_inserted}")
        logger.info(f"Collection statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
    finally:
        ingestion.close()


if __name__ == '__main__':
    main()
