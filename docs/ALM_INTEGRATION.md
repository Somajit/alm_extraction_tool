# ALM Integration Guide

## Overview

ReleaseCraft now integrates directly with ALM (Application Lifecycle Management) to:
- Authenticate users against ALM
- Fetch domains and projects dynamically
- Load test plan folder hierarchy on-demand
- Store user-specific data in MongoDB

## Features

### 1. ALM Authentication
- Users authenticate with their ALM credentials
- Passwords are encrypted using Fernet symmetric encryption
- Credentials are stored in MongoDB (user-specific) while logged in
- Credentials are removed from MongoDB on logout

### 2. Domain and Project Fetching
- After authentication, domains are fetched from ALM REST API
- When a domain is selected, projects are fetched from ALM
- All data is stored in MongoDB with username association

### 3. Test Plan Hierarchy
- Test plan folders are loaded dynamically from ALM
- Initial load fetches root-level folders (parent-id = 0)
- Double-clicking a folder fetches its sub-folders from ALM
- Tree expands/collapses with +/- icons
- All folders are stored in MongoDB (user-specific)

### 4. User-Specific Data
- Each user sees only their own data
- Data isolation ensures security and privacy
- All MongoDB collections include `username` field

## Configuration

### Backend (.env)

```env
# ALM Server Configuration
ALM_BASE_URL=https://your-alm-server.com/qcbin
ALM_ENCRYPTION_KEY=<generate-with-Fernet.generate_key()>
```

### Generate Encryption Key

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

Store the generated key in `.env` file under `ALM_ENCRYPTION_KEY`.

## API Endpoints

### Authentication
```
POST /auth
Body: {"username": "user", "password": "pass"}
Response: {"ok": true, "message": "Authenticated"}
```

### Logout
```
POST /logout
Body: {"username": "user"}
Response: {"ok": true}
```

### Get Domains
```
GET /domains?username=user
Response: [{"name": "Domain1", "id": "Domain1"}]
```

### Get Projects
```
GET /projects?domain=Domain1&username=user
Response: [{"name": "Project1", "id": "Project1"}]
```

### Get Test Folders
```
GET /tree?project=Project1&username=user&domain=Domain1&type=testplan&parent_id=0
Response: {"tree": [{"id": "123", "label": "Folder1", "children": []}]}
```

## MongoDB Collections

### user_credentials
Stores encrypted user credentials while logged in.
```json
{
  "username": "user@example.com",
  "password": "encrypted_password",
  "logged_in": true
}
```

### alm_domains
Stores domains (user-specific).
```json
{
  "name": "DomainA",
  "username": "user@example.com"
}
```

### alm_projects
Stores projects (user-specific).
```json
{
  "name": "Project1",
  "domain": "DomainA",
  "username": "user@example.com"
}
```

### alm_test_folders
Stores test plan folders (user-specific).
```json
{
  "id": "123",
  "name": "Root Folder",
  "parent_id": 0,
  "project": "Project1",
  "domain": "DomainA",
  "username": "user@example.com"
}
```

## ALM REST API Structure

The integration follows HP ALM/Quality Center REST API specifications:

### Authentication (2-Step Process)

**Step 1: Authenticate**
```
POST /qcbin/authentication-point/authenticate
Headers: 
  - Content-Type: application/json
  - Accept: application/json
Auth: Basic Authentication (username:password)
Response: Sets LWSSO_COOKIE_KEY cookie
Status: 200 or 201
```

**Step 2: Create Site Session**
```
POST /qcbin/rest/site-session
Headers:
  - Content-Type: application/json
  - Accept: application/json
Cookies: LWSSO_COOKIE_KEY (from Step 1)
Response: Sets QCSession and XSRF-TOKEN cookies
Status: 200 or 201
```

After authentication, all subsequent API calls use the session cookies.

### Logout (2-Step Process)

**Step 1: End Site Session**
```
DELETE /qcbin/rest/site-session
Headers:
  - Accept: application/json
  - Content-Type: application/json
```

**Step 2: Logout**
```
GET /qcbin/authentication-point/logout
Headers: Accept: application/json
```

### List Domains
```
GET /qcbin/rest/domains
Headers:
  - Accept: application/json
  - Content-Type: application/json
Response: 
{
  "Domains": {
    "Domain": [
      {"Name": "DOMAIN1"},
      {"Name": "DOMAIN2"}
    ]
  }
}
```

### List Projects
```
GET /qcbin/rest/domains/{domain}/projects
Headers:
  - Accept: application/json
  - Content-Type: application/json
Response:
{
  "Projects": {
    "Project": [
      {"Name": "PROJECT1"},
      {"Name": "PROJECT2"}
    ]
  }
}
```

### Get Test Folders
```
GET /qcbin/rest/domains/{domain}/projects/{project}/test-folders
Query Parameters:
  - query={parent-id[0]}  # Root folders
  - query={parent-id[123]} # Sub-folders of folder 123
  - page-size=500
Headers:
  - Accept: application/json
  - Content-Type: application/json
Response:
{
  "entities": [
    {
      "Type": "test-folder",
      "Fields": {
        "Field": [
          {"Name": "id", "values": {"value": ["123"]}},
          {"Name": "name", "values": {"value": ["Root Folder"]}},
          {"Name": "parent-id", "values": {"value": ["0"]}},
          {"Name": "description", "values": {"value": ["Description"]}}
        ]
      }
    }
  ]
}
```

### ALM Query Syntax
ALM uses curly brace query syntax:
- Single field: `{field-name[value]}`
- Multiple conditions: `{field1[value1];field2[value2]}`
- OR condition: `{field[value1 OR value2]}`
- Comparison: `{field[>100]}`, `{field[<50]}`

## Frontend Integration

### Login Flow
1. User enters username/password
2. Frontend calls `/auth` endpoint
3. On success, calls `/domains` to fetch domains
4. User selects domain, calls `/projects`
5. User selects project, navigates to Home page
6. Home page loads root test folders (parent-id=0)

### Tree Interaction
1. Root folders displayed on initial load
2. User double-clicks a folder
3. Frontend calls `/tree` with that folder's ID as parent-id
4. Tree expands to show sub-folders
5. Process repeats for any sub-folder

### Logout
1. User clicks Logout button
2. Frontend calls `/logout` endpoint
3. Backend removes credentials from MongoDB
4. Frontend redirects to login page

## Security Considerations

1. **SSL/TLS**: Enable `verify=True` in ALM session for production
2. **Encryption Key**: Store encryption key securely (environment variable or secrets manager)
3. **Password Storage**: Passwords encrypted at rest in MongoDB
4. **Session Management**: Credentials removed on logout
5. **User Isolation**: All data filtered by username

## Troubleshooting

### Authentication Fails
- Check ALM_BASE_URL is correct
- Verify ALM server is accessible
- Check username/password are correct
- Review backend logs for detailed error messages

### No Domains/Projects Shown
- Verify ALM REST API response structure
- Check MongoDB for stored data
- Review browser console for API errors

### Tree Not Loading
- Check that project, domain, username are passed correctly
- Verify ALM test-folders endpoint
- Check MongoDB alm_test_folders collection

### Encryption Errors
- Ensure ALM_ENCRYPTION_KEY is set in .env
- Key must be valid Fernet key (44 characters base64)

## Development vs Production

### Development (Demo Mode)
- Fallback to local MongoDB sample data if ALM unavailable
- Self-signed certificates allowed (`verify=False`)
- Sample users: admin/admin123

### Production
- ALM authentication required
- Valid SSL certificates (`verify=True`)
- Secure encryption key storage
- Remove fallback demo data

## Installation

Install required dependencies:

```bash
# Backend
cd backend
pip install -r requirements.txt

# Includes: cryptography, requests
```

## Testing

Use the demo mode to test without ALM:

1. Start backend with local MongoDB
2. Use admin/admin123 to login
3. Sample domains/projects will be shown
4. Test tree loading with sample data

Switch to ALM mode:

1. Configure ALM_BASE_URL in .env
2. Use real ALM credentials
3. Data fetched from ALM REST API
4. Stored in MongoDB with user association
