import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import motor.motor_asyncio
from typing import List, Optional

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongo:27017/alm_db')
DEFAULT_ORIGINS = [os.environ.get('CORS_ORIGINS', 'http://localhost:5173')]

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.get_default_database()

app = FastAPI(title='ALM Extraction Tool API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    ok: bool
    message: Optional[str] = None


@app.post('/auth', response_model=AuthResponse)
async def authenticate(payload: AuthRequest):
    user = await db.users.find_one({"username": payload.username})
    if not user:
        raise HTTPException(status_code=401, detail='Invalid username or password')
    # NOTE: For demo we store plaintext passwords. Replace with hashed passwords for production.
    if user.get('password') != payload.password:
        raise HTTPException(status_code=401, detail='Invalid username or password')
    return {"ok": True, "message": "Authenticated"}


@app.get('/domains')
async def get_domains():
    docs = []
    cursor = db.domains.find()
    async for d in cursor:
        docs.append({"name": d.get('name'), "id": str(d.get('_id'))})
    return docs


@app.get('/projects')
async def get_projects(domain: str):
    docs = []
    cursor = db.projects.find({"domain": domain})
    async for p in cursor:
        docs.append({"name": p.get('name'), "id": str(p.get('_id'))})
    return docs


@app.post('/init')
async def init_sample():
    # Create a demo user and sample domains/projects and tree nodes
    await db.users.delete_many({})
    await db.domains.delete_many({})
    await db.projects.delete_many({})
    await db.tree.delete_many({})
    await db.defects.delete_many({})

    await db.users.insert_one({"username": "admin", "password": "admin123"})
    await db.domains.insert_many([
        {"name": "DomainA"},
        {"name": "DomainB"}
    ])
    await db.projects.insert_many([
        {"name": "Project1", "domain": "DomainA"},
        {"name": "Project2", "domain": "DomainA"},
        {"name": "ProjectX", "domain": "DomainB"}
    ])
    # Sample tree nodes for testplan/testlab
    await db.tree.insert_many([
        {"type": "testplan", "project": "Project1", "tree": [
            {"id": "tp1", "label": "Root Plan", "children": [
                {"id": "tp1-1", "label": "Suite 1"},
                {"id": "tp1-2", "label": "Suite 2"}
            ]}
        ]},
        {"type": "testlab", "project": "Project1", "tree": [
            {"id": "tl1", "label": "Execution Root", "children": [
                {"id": "tl1-1", "label": "Cycle 1"}
            ]}
        ]}
    ])

    # Sample defects
    await db.defects.insert_many([
        {"id": "D-1", "summary": "Crash on load", "status": "Open", "priority": "High", "project": "Project1"},
        {"id": "D-2", "summary": "UI glitch", "status": "Closed", "priority": "Low", "project": "Project1"}
    ])

    return {"ok": True}


@app.get('/tree')
async def get_tree(project: str, type: str = 'testplan'):
    doc = await db.tree.find_one({"project": project, "type": type})
    if not doc:
        return {"tree": []}
    return {"tree": doc.get('tree', [])}


@app.get('/defects')
async def get_defects(project: str = None):
    query = {}
    if project:
        query['project'] = project
    docs = []
    cursor = db.defects.find(query)
    async for d in cursor:
        docs.append(d)
    return docs
