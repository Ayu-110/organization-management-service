# System Architecture Diagrams

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│     (Web Browser, Mobile App, Postman, API Testing Tools)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/REST API
                             │ (JSON)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│                      (Port 8000)                                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API ENDPOINTS (Routes)                       │  │
│  │  • POST   /org/create      (Create Organization)         │  │
│  │  • GET    /org/get         (Get Organization)            │  │
│  │  • PUT    /org/update      (Update Organization)         │  │
│  │  • DELETE /org/delete      (Delete Organization)         │  │
│  │  • POST   /admin/login     (Admin Login)                 │  │
│  │  • GET    /                (Health Check)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │         MIDDLEWARE & SECURITY LAYER                      │   │
│  │  • CORS Handler                                          │   │
│  │  • JWT Authentication (Bearer Token)                     │   │
│  │  • Request Validation (Pydantic Models)                  │   │
│  │  • Error Handling & Exception Management                 │   │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │            BUSINESS LOGIC LAYER                          │   │
│  │  • Organization Management                               │   │
│  │  • User Authentication & Authorization                   │   │
│  │  • Password Hashing (Bcrypt)                            │   │
│  │  • JWT Token Generation & Validation                     │   │
│  │  • Collection Name Sanitization                          │   │
│  │  • Data Migration Logic                                  │   │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Motor (Async Driver)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    MONGODB ATLAS (CLOUD)                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MASTER DATABASE                              │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  organizations (Collection)                         │  │  │
│  │  │  ├─ _id (ObjectId)                                  │  │  │
│  │  │  ├─ organization_name (String, Unique Index)        │  │  │
│  │  │  ├─ collection_name (String)                        │  │  │
│  │  │  ├─ created_at (DateTime)                           │  │  │
│  │  │  ├─ updated_at (DateTime)                           │  │  │
│  │  │  └─ status (String)                                 │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  admins (Collection)                                │  │  │
│  │  │  ├─ _id (ObjectId)                                  │  │  │
│  │  │  ├─ email (String, Unique Index)                    │  │  │
│  │  │  ├─ password (String, Hashed with Bcrypt)           │  │  │
│  │  │  ├─ organization_id (String, Reference)             │  │  │
│  │  │  ├─ organization_name (String)                      │  │  │
│  │  │  ├─ role (String)                                   │  │  │
│  │  │  └─ created_at (DateTime)                           │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  org_techcorp (Dynamic Collection)                  │  │  │
│  │  │  └─ Organization-specific data                      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  org_acmeinc (Dynamic Collection)                   │  │  │
│  │  │  └─ Organization-specific data                      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  └─── More dynamic collections (one per organization)... │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Diagrams

### 1. Create Organization Flow

```
┌─────────┐                ┌──────────┐                ┌──────────┐
│ Client  │                │ FastAPI  │                │ MongoDB  │
└────┬────┘                └────┬─────┘                └────┬─────┘
     │                          │                           │
     │ POST /org/create         │                           │
     ├─────────────────────────>│                           │
     │ {org_name, email, pwd}   │                           │
     │                          │                           │
     │                          │ 1. Validate Input         │
     │                          │    (Pydantic)             │
     │                          │                           │
     │                          │ 2. Check if org exists    │
     │                          ├──────────────────────────>│
     │                          │   find_one(org_name)      │
     │                          │<──────────────────────────┤
     │                          │   null (doesn't exist)    │
     │                          │                           │
     │                          │ 3. Hash Password          │
     │                          │    (Bcrypt)               │
     │                          │                           │
     │                          │ 4. Create Org Document    │
     │                          ├──────────────────────────>│
     │                          │   insert_one(org_doc)     │
     │                          │<──────────────────────────┤
     │                          │   {org_id}                │
     │                          │                           │
     │                          │ 5. Create Admin User      │
     │                          ├──────────────────────────>│
     │                          │   insert_one(admin_doc)   │
     │                          │<──────────────────────────┤
     │                          │   success                 │
     │                          │                           │
     │                          │ 6. Create Dynamic         │
     │                          │    Collection             │
     │                          ├──────────────────────────>│
     │                          │   db[org_collection]      │
     │                          │   .insert_one(init_doc)   │
     │                          │<──────────────────────────┤
     │                          │   success                 │
     │                          │                           │
     │  201 Created             │                           │
     │  {org_id, org_name...}   │                           │
     │<─────────────────────────┤                           │
     │                          │                           │
```

---

### 2. Admin Login Flow

```
┌─────────┐                ┌──────────┐                ┌──────────┐
│ Client  │                │ FastAPI  │                │ MongoDB  │
└────┬────┘                └────┬─────┘                └────┬─────┘
     │                          │                           │
     │ POST /admin/login        │                           │
     ├─────────────────────────>│                           │
     │ {email, password}        │                           │
     │                          │                           │
     │                          │ 1. Validate Input         │
     │                          │    (Pydantic)             │
     │                          │                           │
     │                          │ 2. Find Admin by Email    │
     │                          ├──────────────────────────>│
     │                          │   find_one({email})       │
     │                          │<──────────────────────────┤
     │                          │   {admin_doc}             │
     │                          │                           │
     │                          │ 3. Verify Password        │
     │                          │    bcrypt.verify()        │
     │                          │    ✓ Match                │
     │                          │                           │
     │                          │ 4. Generate JWT Token     │
     │                          │    jwt.encode({           │
     │                          │      email, org_id,       │
     │                          │      exp: 30min           │
     │                          │    })                     │
     │                          │                           │
     │  200 OK                  │                           │
     │  {access_token, type}    │                           │
     │<─────────────────────────┤                           │
     │                          │                           │
```

---

### 3. Protected Endpoint Flow (Delete Organization)

```
┌─────────┐                ┌──────────┐                ┌──────────┐
│ Client  │                │ FastAPI  │                │ MongoDB  │
└────┬────┘                └────┬─────┘                └────┬─────┘
     │                          │                           │
     │ DELETE /org/delete       │                           │
     │ + Bearer Token           │                           │
     ├─────────────────────────>│                           │
     │                          │                           │
     │                          │ 1. Extract JWT Token      │
     │                          │    from Authorization     │
     │                          │                           │
     │                          │ 2. Decode & Validate      │
     │                          │    jwt.decode()           │
     │                          │    ✓ Valid & Not Expired  │
     │                          │                           │
     │                          │ 3. Get Current Admin      │
     │                          ├──────────────────────────>│
     │                          │   find_one({email})       │
     │                          │<──────────────────────────┤
     │                          │   {admin_doc}             │
     │                          │                           │
     │                          │ 4. Check Authorization    │
     │                          │    (owns this org?)       │
     │                          │    ✓ Authorized           │
     │                          │                           │
     │                          │ 5. Drop Collection        │
     │                          ├──────────────────────────>│
     │                          │   db[collection].drop()   │
     │                          │<──────────────────────────┤
     │                          │                           │
     │                          │ 6. Delete Org Doc         │
     │                          ├──────────────────────────>│
     │                          │   delete_one({org_name})  │
     │                          │<──────────────────────────┤
     │                          │                           │
     │                          │ 7. Delete Admin(s)        │
     │                          ├──────────────────────────>│
     │                          │   delete_many({org_name}) │
     │                          │<──────────────────────────┤
     │                          │                           │
     │  200 OK                  │                           │
     │  {message: "Deleted"}    │                           │
     │<─────────────────────────┤                           │
     │                          │                           │
```

---

### 4. Update Organization with Data Migration

```
┌─────────┐                ┌──────────┐                ┌──────────┐
│ Client  │                │ FastAPI  │                │ MongoDB  │
└────┬────┘                └────┬─────┘                └────┬─────┘
     │                          │                           │
     │ PUT /org/update          │                           │
     ├─────────────────────────>│                           │
     │ {old_name, new_name,     │                           │
     │  email, password}        │                           │
     │                          │                           │
     │                          │ 1. Verify Admin Creds     │
     │                          ├──────────────────────────>│
     │                          │<──────────────────────────┤
     │                          │                           │
     │                          │ 2. Read Old Collection    │
     │                          ├──────────────────────────>│
     │                          │   find().to_list()        │
     │                          │<──────────────────────────┤
     │                          │   [all_documents]         │
     │                          │                           │
     │                          │ 3. Create New Collection  │
     │                          ├──────────────────────────>│
     │                          │   db[new_collection]      │
     │                          │                           │
     │                          │ 4. Copy All Data          │
     │                          ├──────────────────────────>│
     │                          │   insert_many(documents)  │
     │                          │<──────────────────────────┤
     │                          │                           │
     │                          │ 5. Update Org Metadata    │
     │                          ├──────────────────────────>│
     │                          │   update_one(...)         │
     │                          │<──────────────────────────┤
     │                          │                           │
     │                          │ 6. Drop Old Collection    │
     │                          ├──────────────────────────>│
     │                          │   drop()                  │
     │                          │<──────────────────────────┤
     │                          │                           │
     │  200 OK                  │                           │
     │<─────────────────────────┤                           │
     │                          │                           │
```

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       main.py (FastAPI App)                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Configuration Layer                                         │ │
│  │  • Environment variables loading (.env)                     │ │
│  │  • MongoDB connection setup                                 │ │
│  │  • JWT secret key configuration                             │ │
│  │  • CORS middleware setup                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Data Models (Pydantic)                                      │ │
│  │  • OrganizationCreate                                       │ │
│  │  • OrganizationUpdate                                       │ │
│  │  • OrganizationDelete                                       │ │
│  │  • AdminLogin                                               │ │
│  │  • Token                                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Helper Functions                                            │ │
│  │  • hash_password()         - Bcrypt hashing                 │ │
│  │  • verify_password()       - Password verification          │ │
│  │  • create_access_token()   - JWT generation                 │ │
│  │  • sanitize_collection()   - Name sanitization              │ │
│  │  • get_current_admin()     - Auth dependency                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ API Endpoints (Route Handlers)                              │ │
│  │  • POST   /org/create                                       │ │
│  │  • GET    /org/get                                          │ │
│  │  • PUT    /org/update                                       │ │
│  │  • DELETE /org/delete                                       │ │
│  │  • POST   /admin/login                                      │ │
│  │  • GET    /                                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Lifecycle Events                                            │ │
│  │  • startup_event()   - Create database indexes              │ │
│  │  • shutdown_event()  - Close database connections           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       SECURITY LAYERS                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Layer 1: Input Validation                                   │ │
│  │  • Pydantic models validate all inputs                      │ │
│  │  • Type checking (EmailStr, String length, etc.)            │ │
│  │  • Prevents injection attacks                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Layer 2: Authentication                                      │ │
│  │  • JWT tokens with expiration (30 minutes)                  │ │
│  │  • Bearer token in Authorization header                     │ │
│  │  • Token contains: email, org_id, role                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Layer 3: Authorization                                       │ │
│  │  • Verify user owns the organization                        │ │
│  │  • Protected endpoints check permissions                    │ │
│  │  • Delete operation requires authentication                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Layer 4: Data Protection                                     │ │
│  │  • Passwords hashed with Bcrypt (12 rounds)                 │ │
│  │  • Never store plain text passwords                         │ │
│  │  • Unique indexes prevent duplicates                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Layer 5: Database Security                                   │ │
│  │  • MongoDB Atlas with authentication                        │ │
│  │  • IP whitelist for connections                             │ │
│  │  • Encrypted connections (SSL/TLS)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
1. CREATE ORGANIZATION
   Client → FastAPI → Validate → Check Duplicate → Hash Password
        → Create Org → Create Admin → Create Collection → Return Success

2. GET ORGANIZATION
   Client → FastAPI → Validate → Query MongoDB → Return Org Data

3. ADMIN LOGIN
   Client → FastAPI → Validate → Find Admin → Verify Password
        → Generate JWT → Return Token

4. UPDATE ORGANIZATION
   Client → FastAPI → Validate → Auth Check → Create New Collection
        → Copy Data → Update Metadata → Drop Old → Return Success

5. DELETE ORGANIZATION (Protected)
   Client → FastAPI → Verify JWT → Auth Check → Drop Collection
        → Delete Org → Delete Admins → Return Success
```

---

## Technology Stack

```
┌──────────────────────────────────────────────────────┐
│ Frontend/Client                                       │
│  • Any HTTP Client (Browser, Mobile App, Postman)    │
└──────────────────────────────────────────────────────┘
                        ↓ HTTP/REST
┌──────────────────────────────────────────────────────┐
│ Backend Framework                                     │
│  • FastAPI 0.109.0 (Python 3.8+)                     │
│  • Uvicorn (ASGI Server)                             │
│  • Pydantic (Data Validation)                        │
└──────────────────────────────────────────────────────┘
                        ↓ Motor Driver
┌──────────────────────────────────────────────────────┐
│ Database                                              │
│  • MongoDB Atlas (Cloud)                              │
│  • Motor (Async Driver)                               │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Authentication & Security                             │
│  • JWT (python-jose)                                  │
│  • Bcrypt (passlib)                                   │
└──────────────────────────────────────────────────────┘
```