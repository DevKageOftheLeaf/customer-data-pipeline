import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
import traceback
from services.ingestion import ingest_customers
from database import SessionLocal
from models.customer import Customer
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Customer Data Pipeline", version="1.0.0")

# Pydantic models for request/response
class CustomerBase(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None  # Changed to string to match DB
    account_balance: Optional[float] = None
    created_at: Optional[str] = None     # Changed to string to match DB

class CustomerResponse(CustomerBase):
    # For Pydantic v2 compatibility
    model_config = {"from_attributes": True}

class IngestResponse(BaseModel):
    status: str
    records_processed: int

@app.post("/api/ingest", response_model=IngestResponse)
def ingest_data():
    """Fetch all data from Flask and upsert into PostgreSQL"""
    try:
        result = ingest_customers()
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.get("/api/customers", response_model=dict)
def get_customers(page: int = 1, limit: int = 10):
    """Get paginated customers from database"""
    try:
        # Validate parameters
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10
        if limit > 100:
            limit = 100
            
        db = SessionLocal()
        try:
            # Get total count
            total = db.query(Customer).count()
            
            # Get paginated results
            offset = (page - 1) * limit
            customers = db.query(Customer).offset(offset).limit(limit).all()
            
            # Convert to dict for response
            customer_list = []
            for customer in customers:
                try:
                    customer_list.append({
                        "customer_id": customer.customer_id,
                        "first_name": customer.first_name,
                        "last_name": customer.last_name,
                        "email": customer.email,
                        "phone": customer.phone,
                        "address": customer.address,
                        "date_of_birth": str(customer.date_of_birth) if customer.date_of_birth else None,
                        "account_balance": float(customer.account_balance) if customer.account_balance else None,
                        "created_at": str(customer.created_at) if customer.created_at else None
                    })
                except Exception as inner_e:
                    logger.error(f"Error processing customer {customer.customer_id}: {inner_e}")
                    logger.error(traceback.format_exc())
                    raise
            
            return {
                "data": customer_list,
                "total": total,
                "page": page,
                "limit": limit
            }
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching customers: {str(e)}")

@app.get("/api/customers/{customer_id}", response_model=dict)
def get_customer(customer_id: str):
    """Get single customer by ID"""
    try:
        db = SessionLocal()
        try:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
                
            return {
                "data": {
                    "customer_id": customer.customer_id,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "address": customer.address,
                    "date_of_birth": str(customer.date_of_birth) if customer.date_of_birth else None,
                    "account_balance": float(customer.account_balance) if customer.account_balance else None,
                    "created_at": str(customer.created_at) if customer.created_at else None
                }
            }
        finally:
            db.close()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching customer: {str(e)}")

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
