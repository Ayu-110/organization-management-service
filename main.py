from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration - HARDCODED FOR NOW
MONGODB_URL = "mongodb+srv://<Database_name>:<password>@cluster0.vhd1wyh.mongodb.net/?appName=Cluster0"
SECRET_KEY = "anylongstring"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize FastAPI app
app = FastAPI(
    title="Organization Management Service",
    description="Multi-tenant organization management API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB client
client = AsyncIOMotorClient(MONGODB_URL)
master_db = client["master_database"]
organizations_collection = master_db["organizations"]
admins_collection = master_db["admins"]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()


# Pydantic Models
class OrganizationCreate(BaseModel):
    organization_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class OrganizationUpdate(BaseModel):
    organization_name: str
    new_organization_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str


class OrganizationGet(BaseModel):
    organization_name: str


class OrganizationDelete(BaseModel):
    organization_name: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# Helper Functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def sanitize_collection_name(name: str) -> str:
    """Sanitize organization name for MongoDB collection name"""
    return f"org_{name.lower().replace(' ', '_').replace('-', '_')}"


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated admin"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        org_id: str = payload.get("org_id")
        if email is None or org_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return {"email": email, "org_id": org_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Organization Management Service",
        "version": "1.0.0"
    }


@app.post("/org/create", status_code=status.HTTP_201_CREATED)
async def create_organization(org_data: OrganizationCreate):
    """Create a new organization with admin user"""
    
    # Check if organization already exists
    existing_org = await organizations_collection.find_one(
        {"organization_name": org_data.organization_name}
    )
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization name already exists"
        )
    
    # Check if admin email already exists
    existing_admin = await admins_collection.find_one({"email": org_data.email})
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email already exists"
        )
    
    # Generate collection name
    collection_name = sanitize_collection_name(org_data.organization_name)
    
    # Create organization document
    org_document = {
        "organization_name": org_data.organization_name,
        "collection_name": collection_name,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status": "active"
    }
    
    # Insert organization into master database
    org_result = await organizations_collection.insert_one(org_document)
    org_id = str(org_result.inserted_id)
    
    # Hash password
    hashed_password = hash_password(org_data.password)
    
    # Create admin user
    admin_document = {
        "email": org_data.email,
        "password": hashed_password,
        "organization_id": org_id,
        "organization_name": org_data.organization_name,
        "role": "admin",
        "created_at": datetime.utcnow()
    }
    
    await admins_collection.insert_one(admin_document)
    
    # Create dynamic collection for the organization
    org_collection = master_db[collection_name]
    
    # Initialize with a sample schema document (optional)
    await org_collection.insert_one({
        "initialized": True,
        "created_at": datetime.utcnow(),
        "type": "initialization"
    })
    
    return {
        "message": "Organization created successfully",
        "organization_id": org_id,
        "organization_name": org_data.organization_name,
        "collection_name": collection_name,
        "admin_email": org_data.email
    }


@app.get("/org/get")
async def get_organization(organization_name: str):
    """Get organization details by name"""
    
    organization = await organizations_collection.find_one(
        {"organization_name": organization_name},
        {"_id": 0, "created_at": 1, "updated_at": 1, "organization_name": 1, 
         "collection_name": 1, "status": 1}
    )
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Convert datetime to string for JSON serialization
    organization["created_at"] = organization["created_at"].isoformat()
    organization["updated_at"] = organization["updated_at"].isoformat()
    
    return {
        "message": "Organization retrieved successfully",
        "organization": organization
    }


@app.put("/org/update")
async def update_organization(org_data: OrganizationUpdate):
    """Update organization name and migrate data to new collection"""
    
    # Find existing organization
    existing_org = await organizations_collection.find_one(
        {"organization_name": org_data.organization_name}
    )
    
    if not existing_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Verify admin credentials
    admin = await admins_collection.find_one({"email": org_data.email})
    if not admin or admin["organization_name"] != org_data.organization_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Invalid admin credentials"
        )
    
    if not verify_password(org_data.password, admin["password"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Invalid password"
        )
    
    # Check if new organization name already exists
    if org_data.new_organization_name != org_data.organization_name:
        existing_new_org = await organizations_collection.find_one(
            {"organization_name": org_data.new_organization_name}
        )
        if existing_new_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New organization name already exists"
            )
    
    # Get old collection name
    old_collection_name = existing_org["collection_name"]
    new_collection_name = sanitize_collection_name(org_data.new_organization_name)
    
    # Copy data from old collection to new collection
    old_collection = master_db[old_collection_name]
    new_collection = master_db[new_collection_name]
    
    # Get all documents from old collection
    documents = await old_collection.find().to_list(length=None)
    
    if documents:
        await new_collection.insert_many(documents)
    
    # Update organization in master database
    await organizations_collection.update_one(
        {"organization_name": org_data.organization_name},
        {
            "$set": {
                "organization_name": org_data.new_organization_name,
                "collection_name": new_collection_name,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Update admin's organization reference
    await admins_collection.update_one(
        {"email": org_data.email},
        {"$set": {"organization_name": org_data.new_organization_name}}
    )
    
    # Drop old collection
    await old_collection.drop()
    
    return {
        "message": "Organization updated successfully",
        "old_name": org_data.organization_name,
        "new_name": org_data.new_organization_name,
        "new_collection_name": new_collection_name
    }


@app.delete("/org/delete")
async def delete_organization(
    org_data: OrganizationDelete,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete organization (authenticated users only)"""
    
    # Find organization
    organization = await organizations_collection.find_one(
        {"organization_name": org_data.organization_name}
    )
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Verify that current admin belongs to this organization
    admin = await admins_collection.find_one({"email": current_admin["email"]})
    if admin["organization_name"] != org_data.organization_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: You can only delete your own organization"
        )
    
    # Drop the organization's collection
    collection_name = organization["collection_name"]
    await master_db[collection_name].drop()
    
    # Delete organization from master database
    await organizations_collection.delete_one(
        {"organization_name": org_data.organization_name}
    )
    
    # Delete all admins associated with this organization
    await admins_collection.delete_many(
        {"organization_name": org_data.organization_name}
    )
    
    return {
        "message": "Organization deleted successfully",
        "organization_name": org_data.organization_name
    }


@app.post("/admin/login", response_model=Token)
async def admin_login(credentials: AdminLogin):
    """Admin login endpoint returning JWT token"""
    
    # Find admin by email
    admin = await admins_collection.find_one({"email": credentials.email})
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, admin["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": admin["email"],
            "org_id": admin["organization_id"],
            "org_name": admin["organization_name"],
            "role": admin["role"]
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Create indexes on startup"""
    await organizations_collection.create_index("organization_name", unique=True)
    await admins_collection.create_index("email", unique=True)
    print("✅ Database indexes created successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    client.close()
    print("✅ Database connection closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
