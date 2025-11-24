# SSH Tunneling Debug Fix

## Problem Identified

When using SSH tunneling from an HPC server to your Macbook, setting the data directory failed with "Failed to set data directory". 

### Root Cause

The issue was a **client/server filesystem mismatch**:

1. **Backend runs on HPC server** (where your data is located)
2. **Frontend runs in browser on Macbook** (your local machine)
3. When you enter a data directory path, the backend validates it on the **HPC server's filesystem**
4. If you entered a Macbook path (e.g., `/Users/...`), the HPC server couldn't find it → returned 404 error
5. The frontend showed a generic error message that didn't explain the issue

## Fixes Implemented

### 1. Backend Improvements (`backend/main.py`)

- ✅ Added hostname information to error messages
- ✅ Clear explanation that path must exist on server machine
- ✅ New `/api/server_info` endpoint to show backend server details
- ✅ Root endpoint (`/`) now returns server hostname and current data directory

### 2. Frontend Improvements (`frontend/src/App.jsx`)

- ✅ Display backend server hostname prominently in the UI
- ✅ Show current data directory on the backend server
- ✅ Updated placeholder text to show server hostname
- ✅ Better error messages that explain the path must exist on the server
- ✅ Fetch and display server info on app load

### 3. Documentation Updates (`README.md`)

- ✅ Expanded SSH tunneling section with clear step-by-step instructions
- ✅ Added warning about data directory path requirements
- ✅ Explained how the client/server architecture works
- ✅ Provided example paths for HPC servers

## How to Use (SSH Tunneling from HPC to Macbook)

### On the HPC Server:

```bash
# Terminal 1: Start backend
cd /path/to/vis-tool-3d/backend
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd /path/to/vis-tool-3d/frontend
npm run dev
```

### On Your Macbook:

```bash
# Create SSH tunnel
ssh -L 5173:localhost:5173 -L 8000:localhost:8000 user@hpc-server.domain.edu

# Then open browser to:
http://localhost:5173
```

### Setting the Data Directory:

**Important:** Enter a path that exists on the **HPC server**, not your Macbook!

- ✅ Good: `/scratch/username/simulations/`
- ✅ Good: `/home/username/data/`
- ❌ Bad: `/Users/cche/Desktop/data/` (this is a Macbook path!)
- ❌ Bad: `C:\Users\...` (this is a Windows path!)

The UI will now show:
- **Backend hostname**: Which server the backend is running on
- **Current data directory**: What directory is currently configured

## Testing the Fix

1. Start the backend and frontend on your HPC server
2. Create SSH tunnel from your Macbook
3. Open the web interface
4. Check that you see the backend hostname (e.g., "Backend: hpc-login-01")
5. Enter a valid HPC path (e.g., `/scratch/yourusername/data/`)
6. Click "Set" - should now work!
7. If it fails, the error message will now clearly show:
   - Which server is checking the path
   - That the path must exist on that server

## Why It Works Now

| Component | Location | Filesystem |
|-----------|----------|------------|
| Backend (Python/FastAPI) | HPC Server | HPC filesystem |
| Frontend (React/Vite) | Macbook Browser | N/A (just UI) |
| Data Files | HPC Server | HPC filesystem |

The backend validates paths on its own filesystem (HPC), so you must provide HPC paths. The new UI makes this clear by showing the backend hostname.

## Additional Improvements

The fix also includes:
- Better debugging information (server hostname in all responses)
- Clearer error messages throughout
- Visual feedback about which server is being used
- Updated documentation with examples

