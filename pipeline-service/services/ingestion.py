import dlt
import requests
from typing import Dict, Any
import logging
import os
from database import SessionLocal
from models.customer import Customer

logger = logging.getLogger(__name__)

def get_flask_data():
    """Fetch all data from Flask API handling pagination using dlt-compatible approach"""
    flask_url = "http://mock-server:5000"
    all_customers = []
    page = 1
    limit = 100  # Maximum limit per page
    
    while True:
        try:
            response = requests.get(
                f"{flask_url}/api/customers",
                params={"page": page, "limit": limit},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            customers = data.get("data", [])
            if not customers:
                break
                
            all_customers.extend(customers)
            
            # Check if we've fetched all data
            total = data.get("total", 0)
            if len(all_customers) >= total:
                break
                
            page += 1
            
        except requests.RequestException as e:
            logger.error(f"Error fetching customers from Flask API: {e}")
            raise
    
    logger.info(f"Fetched {len(all_customers)} customers from Flask API")
    return all_customers

def load_to_postgres(data):
    """Load data into PostgreSQL using dlt pipeline"""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/customer_db")
    
    # Create dlt pipeline with explicit credentials
    pipeline = dlt.pipeline(
        pipeline_name="customer_ingestion",
        destination=dlt.destinations.postgres(
            credentials=database_url
        ),
        dataset_name="customer_data",
        progress="log"
    )
    
    # Run the pipeline with our data
    load_info = pipeline.run(data, table_name="customers")
    logger.info(f"Loaded data into PostgreSQL: {load_info}")
    return load_info

def ingest_customers() -> Dict[str, Any]:
    """Main ingestion process using dlt"""
    try:
        # Fetch all customers from Flask
        customers = get_flask_data()
        
        # Load to PostgreSQL using dlt
        load_info = load_to_postgres(customers)
        
        logger.info(f"Successfully ingested {len(customers)} customers")
        
        return {
            "status": "success",
            "records_processed": len(customers)
        }
        
    except Exception as e:
        logger.error(f"Error during ingestion process: {e}")
        raise
