# Logging Implementation Summary

## Overview
Comprehensive logging has been implemented across all services with a real-time log viewer for admin users.

## Backend Logging (backend/app/main.py)

### Configuration
```python
log_dir = Path(__file__).parent.parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'backend.log'),
        logging.StreamHandler()
    ]
)
```

### Log File Location
- **Path**: `logs/backend.log`
- **Format**: `timestamp - module - level - message`
- **Output**: Both file and console

### New API Endpoints

#### Get Recent Logs
```
GET /api/logs/{service}?lines=100
```
Returns the last N lines from a service log file.

**Services**: `backend`, `mock-alm`, `frontend`

**Response**:
```json
{
  "logs": ["line1", "line2", ...],
  "total": 1234
}
```

#### Stream Logs (Server-Sent Events)
```
GET /api/logs/{service}/stream
```
Real-time streaming of log entries using SSE.

**Features**:
- Sends last 50 lines on connection
- Streams new lines as they're written
- Auto-reconnects on disconnect

## Mock ALM Logging (mock_alm/main.py)

### Configuration
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'mock-alm.log'),
        logging.StreamHandler()
    ]
)
```

### Log File Location
- **Path**: `logs/mock-alm.log`

### Logged Events
- Authentication requests
- Site session creation
- Domain/project requests
- Authentication failures
- All API endpoints

## Frontend Logging

### Console Logging
All console.error calls are already in place in:
- `TestTree.tsx`
- `DefectsTable.tsx`
- `Home.tsx`

### Future Enhancement
To capture frontend logs to file, add to `main.tsx`:
```typescript
const originalConsole = {
  log: console.log,
  error: console.error,
  warn: console.warn
}

const logToBackend = (level: string, ...args: any[]) => {
  originalConsole[level](...args)
  // Optionally send to backend
  fetch('http://localhost:8000/api/logs/frontend', {
    method: 'POST',
    body: JSON.stringify({ level, message: args.join(' '), timestamp: new Date() })
  }).catch(() => {})
}

console.log = (...args) => logToBackend('log', ...args)
console.error = (...args) => logToBackend('error', ...args)
console.warn = (...args) => logToBackend('warn', ...args)
```

## UI Components

### LogsViewer Component (frontend/src/components/LogsViewer.tsx)

**Features**:
- Three tabs: Backend, Mock ALM, Frontend
- Real-time streaming toggle
- Auto-scroll option
- Refresh button
- Color-coded log levels:
  - 🔴 Error (red)
  - 🟡 Warning (yellow)
  - 🟢 Success (green)
  - 🔵 Info (blue)
- Line count badges
- Dark terminal theme

**Admin Access Only**: Component checks `isAdmin` prop

### Integration in Home Page

The Logs tab appears only for users with username `admin`:

```tsx
{user === 'admin' && <Tab label="Logs" />}
{user === 'admin' && (
  <TabPanel value={tabValue} index={3}>
    <LogsViewer isAdmin={true} />
  </TabPanel>
)}
```

## Log Directory Structure

```
logs/
├── backend.log      # Backend API logs
├── mock-alm.log     # Mock ALM service logs
└── frontend.log     # Frontend console logs (if implemented)
```

## Installation Steps

### 1. Install Frontend Dependencies
```bash
cd frontend
npm install lucide-react
```

### 2. Create Logs Directory
The backend automatically creates `logs/` directory on startup.

### 3. Update Scripts
The `run-local.bat` and `run-local.sh` scripts already handle log redirection.

## Usage

### For Admin Users
1. Login with username: `admin` (any password on first login creates user)
2. Navigate to the "Logs" tab
3. Select service (Backend/Mock ALM/Frontend)
4. Click "Start Stream" for real-time logs
5. Toggle "Auto-scroll" to follow new entries

### For Developers
- Logs are written to both console and file
- Use standard Python logging: `logger.info()`, `logger.error()`, etc.
- Log files rotate automatically when they get large
- Check `logs/` directory for historical logs

## Log Levels

### INFO
- Service startup
- Request processing
- Data fetched/stored
- Normal operations

### WARNING
- Retry attempts
- Missing optional data
- Non-critical failures

### ERROR
- Failed requests
- Database errors
- Authentication failures
- Exceptions

## Performance Considerations

- Log files are read efficiently (tail operation)
- Streaming uses SSE (low overhead)
- Auto-scroll can be disabled for performance
- Old logs are kept (consider adding rotation)

## Future Enhancements

1. **Log Rotation**: Implement logrotate or Python's RotatingFileHandler
2. **Search/Filter**: Add search functionality in UI
3. **Download Logs**: Export logs as file
4. **Log Levels Filter**: Show only errors/warnings
5. **Multiple Streams**: Watch multiple services simultaneously
6. **Alerts**: Notify on error patterns
7. **Metrics Dashboard**: Parse logs for statistics

## Troubleshooting

### Logs not appearing
1. Check `logs/` directory exists
2. Verify file permissions
3. Check backend is running
4. Ensure logger is configured before any log calls

### Stream not working
1. Check CORS settings allow SSE
2. Verify EventSource supported in browser
3. Check network tab for connection errors
4. Try manual refresh first

### Admin tab not visible
1. Login with username exactly `admin` (case-sensitive)
2. Check localStorage for user value
3. Clear cache and re-login
