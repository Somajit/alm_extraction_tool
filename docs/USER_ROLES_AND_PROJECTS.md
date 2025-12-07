# User Roles and Project Management Implementation

## Overview
Implemented role-based access control with separate user workflows for regular users and administrators.

## User Model Changes

### Backend (MongoDB Users Collection)
```python
{
  "username": str,
  "password": str,
  "email": str,
  "role": "user" | "admin",  # NEW
  "projects": [               # NEW
    {
      "domain": str,
      "project": str,
      "added_at": datetime
    }
  ],
  "created_at": datetime
}
```

### Authentication Updates
- **Default Role**: New users get "user" role automatically
- **Admin Creation**: Username "admin" (case-insensitive) gets "admin" role
- **Response**: Auth endpoint now returns `role` and `projects` array

## New Backend APIs

### User Profile
```
GET /api/users/profile?username={username}
Returns: { username, email, role, projects[], created_at }
```

### Add Project to User
```
POST /api/users/projects?username={}&domain={}&project={}
Returns: { success, message }
```

### Remove Project from User
```
DELETE /api/users/projects?username={}&domain={}&project={}
Returns: { success, message }
```

### Admin: Get All Users
```
GET /api/admin/users?admin_username={}
Returns: { users: [...] }
Requires: admin role
```

### Admin: Update User Role
```
PUT /api/admin/users/role?admin_username={}&target_username={}&new_role={}
Returns: { success, message }
Requires: admin role
Restrictions: Cannot change own role
```

### Admin: Clean User Data
```
DELETE /api/admin/users/data?admin_username={}&target_username={}
Returns: { success, message, deleted_counts }
Requires: admin role
Restrictions: Cannot clean own data
```

Cleans data from collections:
- domains, projects
- testplan_folders, testplan_tests
- testlab_folders, testlab_testsets, testlab_tests
- test_runs, defects, releases
- user_credentials

## Frontend Pages

### 1. Login Page (Updated)
**Path**: `/` (when not authenticated)

**Changes**:
- Simplified to single-step authentication
- No domain/project selection
- Returns role and projects from backend
- Stores username and role in localStorage

**Flow**:
```
Enter credentials → Authenticate → 
  If admin: Redirect to AdminDashboard
  If user with no projects: Redirect to UserSetup
  If user with projects: Redirect to Home
```

### 2. UserSetup Page (NEW)
**Path**: `/setup`
**Access**: Regular users only (role: "user")

**Features**:
- Fetch domains from ALM
- Select domain → loads projects
- Add projects to user's access list
- View all added projects
- Remove projects from list
- Continue button (requires at least 1 project)

**Components**:
- Domain dropdown (fetches from `/api/get_domains`)
- Project dropdown (fetches from `/api/get_projects`)
- Projects list with delete buttons
- Add project button
- Continue to app button

**Navigation**:
- After adding first project → Can proceed to Home
- Stores first project as default in localStorage

### 3. Home Page (Updated)
**Path**: `/home`
**Access**: Regular users with projects

**Changes**:
- Removed admin-specific Logs tab
- Only shows TestPlan, TestLab, Defects tabs
- For regular users only

### 4. AdminDashboard (NEW)
**Path**: `/admin`
**Access**: Admin users only (role: "admin")

**Features**:

#### Tab 1: User Management
- **User Table**: Lists all users with:
  - Username
  - Email
  - Role badge (color-coded)
  - Projects list
  - Created date
  - Actions (Edit/Delete)

- **Edit Role**: 
  - Modal dialog to change user role
  - Admin cannot change own role
  - Options: user, admin

- **Clean User Data**:
  - Modal with warning
  - Shows what will be deleted
  - Admin cannot delete own data
  - Returns deleted counts per collection

#### Tab 2: System Logs
- Embedded LogsViewer component
- Real-time log streaming
- Backend, Mock ALM, Frontend logs

**Admin Restrictions**:
- Cannot see TestPlan/TestLab/Defects tabs
- Cannot access regular Home page
- Only sees AdminDashboard

## Routing Logic (App.tsx)

```typescript
If not authenticated:
  → Login Page

If authenticated:
  If role === "admin":
    → AdminDashboard (/admin)
    All routes redirect to /admin
  
  Else (role === "user"):
    If no projects:
      → UserSetup (/setup)
      All routes redirect to /setup
    Else:
      → Home (/home)
      All routes redirect to /home
```

## User Workflows

### New Regular User Workflow
1. Login with username/password
2. Backend creates user with role: "user", projects: []
3. Frontend redirects to UserSetup
4. User adds domain/project combinations
5. User clicks "Continue"
6. Frontend stores first project as default
7. Redirects to Home page
8. Can use TestPlan, TestLab, Defects

### New Admin User Workflow
1. Login with username "admin" and any password
2. Backend creates user with role: "admin"
3. Frontend redirects to AdminDashboard
4. Admin sees:
   - User Management tab (list users, change roles, clean data)
   - System Logs tab (real-time logs from all services)
5. Admin never sees TestPlan/TestLab/Defects

### Existing User Workflow
1. Login with username/password
2. Backend returns existing user with role and projects
3. Frontend routes based on role and projects:
   - Admin → AdminDashboard
   - User with projects → Home
   - User without projects → UserSetup

## Security Features

### Role Checks
- All admin endpoints verify requester has admin role
- 403 Forbidden if non-admin tries to access admin APIs

### Self-Protection
- Admin cannot change own role
- Admin cannot delete own data
- Prevents accidental lockout

### Data Isolation
- Regular users can only manage their own projects
- Admin can manage all users' data
- Clean data operation is atomic per user

## UI Components Created

### UserSetup.tsx
- Material-UI Card layout
- Domain/Project selectors
- Project list with delete actions
- Success/Error alerts
- Loading states

### AdminDashboard.tsx
- Two-tab layout
- User table with actions
- Role edit modal
- Delete data confirmation modal
- Embedded LogsViewer
- Color-coded role badges

### Updated Components
- **App.tsx**: Role-based routing
- **Login.tsx**: Simplified auth flow
- **Home.tsx**: Removed admin features

## Storage Keys (localStorage)

```typescript
user: string          // Username
role: string          // "user" | "admin"
domain: string        // Current domain (for regular users)
project: string       // Current project (for regular users)
```

## Database Collections

### users
Primary collection for user management
- Indexed on: username (unique)

### All data collections
Filtered by "user" field for data isolation:
- domains, projects
- testplan_folders, testplan_tests
- testlab_folders, testlab_testsets, testlab_tests  
- test_runs, defects, releases
- user_credentials

## Installation & Setup

### Backend
No additional dependencies needed. All endpoints added to existing `main.py`.

### Frontend
No additional dependencies needed. Uses existing Material-UI components.

## Testing Scenarios

### Create Admin User
1. Login with username: "admin", password: any (e.g., "admin123")
2. Verify redirected to AdminDashboard
3. Check User Management tab shows all users
4. Check System Logs tab shows logs

### Create Regular User
1. Login with username: "testuser", password: "password"
2. Verify redirected to UserSetup
3. Add a project (domain/project)
4. Click Continue
5. Verify redirected to Home with TestPlan/TestLab/Defects tabs

### Admin Changes User Role
1. Login as admin
2. Go to User Management tab
3. Click Edit icon on a regular user
4. Change role to "admin"
5. Logout and login as that user
6. Verify now sees AdminDashboard

### Admin Cleans User Data
1. Login as admin
2. Go to User Management tab
3. Click Delete icon on a user
4. Confirm deletion
5. Verify success message with deleted counts
6. Login as that user
7. Verify all data is gone (empty TestPlan, etc.)

## Future Enhancements

1. **Password Encryption**: Hash passwords with bcrypt
2. **Email Notifications**: Notify users when role changes
3. **Audit Log**: Track admin actions
4. **Project Permissions**: Fine-grained permissions per project
5. **User Groups**: Create groups with shared projects
6. **Bulk Operations**: Admin bulk role change, bulk delete
7. **User Search/Filter**: Search users by name/role in admin dashboard
8. **Project Templates**: Pre-defined project access sets
9. **Self-Service**: Users request project access, admin approves
10. **Session Management**: Track active sessions, force logout
