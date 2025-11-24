# Comprehensive Debugging Guide

## New Debugging Features Added

### Backend (Python/FastAPI)
- ✅ **Detailed logging** for all requests
- ✅ **Request/response middleware** that logs every HTTP request
- ✅ **Extensive logging** in `/api/set_data_dir` endpoint
- ✅ **New test endpoint** `/api/test_path` to check paths
- ✅ **Enhanced server info** with more details
- ✅ **Log file created**: `backend_debug.log` in backend directory

### Frontend (React)
- ✅ **Console logging** for all operations
- ✅ **Detailed request/response logging**
- ✅ **"Test" button** to check if path exists before setting
- ✅ **Better error messages** with full details

## How to Debug

### Step 1: Start Backend with Logging

```bash
cd backend
source ../venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Watch the terminal output** - you'll now see detailed logs like:

```
2024-11-24 12:34:56 - __main__ - INFO - ====== Incoming Request ======
2024-11-24 12:34:56 - __main__ - INFO - Method: POST
2024-11-24 12:34:56 - __main__ - INFO - URL: http://localhost:8000/api/set_data_dir
2024-11-24 12:34:56 - __main__ - INFO - Body: {"path":"/some/path"}
```

### Step 2: Start Frontend

```bash
cd frontend
npm run dev
```

### Step 3: Open Browser Console

1. Open your browser to `http://localhost:5173`
2. Open Developer Tools (F12 or Cmd+Option+I on Mac)
3. Go to the **Console** tab
4. **Keep it open** while you try to set the data directory

### Step 4: Use the Test Button

**Before** setting a data directory:

1. Enter the path in the text field
2. Click the **"Test"** button
3. A popup will show you detailed information:
   ```json
   {
     "path": "/your/path/here",
     "is_absolute": true,
     "exists": true,
     "is_dir": true,
     "can_read": true,
     "server_hostname": "hpc-login-01"
   }
   ```

This tells you:
- If the path exists on the **server**
- If it's a directory
- If you can read it
- What server it's checking

### Step 5: Try Setting the Directory

Click "Set" and watch:

**In Browser Console:**
```
========================================
handleSetDataDir called
dataDir value: /your/path/here
dataDir type: string
Request body: {path: "/your/path/here"}
Sending POST request to /api/set_data_dir
Response status: 200
Success response data: {message: "...", path: "..."}
========================================
```

**In Backend Terminal:**
```
================================================================================
SET_DATA_DIR endpoint called
Received request object: DataDirRequest(path='/your/path/here')
Backend server hostname: hpc-login-01
Current working directory: /home/user/vis-tool-3d/backend
Current DATA_DIR value: /home/user/vis-tool-3d/data
Attempting to set data directory to: /your/path/here
Checking if path exists: /your/path/here
os.path.exists(/your/path/here) = True
Checking if path is a directory: /your/path/here
os.path.isdir(/your/path/here) = True
Successfully listed directory, found 42 items
Successfully changed DATA_DIR from '/old/path' to '/your/path/here'
================================================================================
```

## What to Look For

### If You See "Directory not found" Error

**Backend logs will show:**
```
Path does not exist: /your/path/here
Parent directory: /your/path
Parent directory contents: ['file1', 'file2', ...]
```

**This means:**
- The path doesn't exist on the **backend server**
- Check you're using the right machine's path
- Use the "Test" button to verify

### If You See "Path is not a directory" Error

**Backend logs will show:**
```
os.path.isdir(/your/path/here) = False
```

**This means:**
- The path exists but it's a file, not a directory
- Double-check the path

### If You See Network Errors

**Browser console will show:**
```
Exception caught in handleSetDataDir
Error type: TypeError
Error message: Failed to fetch
```

**This means:**
- Backend is not running
- Or SSH tunnel is not working
- Or wrong port

## Log Files

### Backend Log File

A file `backend_debug.log` is created in the backend directory with all debug information.

```bash
# View the log file
cd backend
tail -f backend_debug.log
```

Or open it in an editor to see the full history.

### Browser Console Log

You can save the browser console output:
1. Right-click in the console
2. Select "Save as..." or copy the text

## Common Issues and What You'll See

### Issue: Using Local Path Instead of Server Path

**Test Button Result:**
```json
{
  "exists": false,
  "server_hostname": "hpc-server",
  "path": "/Users/cche/Desktop/data"  ← This is a Mac path!
}
```

**Backend Log:**
```
Path does not exist: /Users/cche/Desktop/data
```

**Solution:** Use a path that exists on `hpc-server`, like `/scratch/username/data`

### Issue: Backend Not Reachable

**Browser Console:**
```
Failed to fetch
net::ERR_CONNECTION_REFUSED
```

**Solution:** 
- Check backend is running: `curl http://localhost:8000/`
- Check SSH tunnel: `ssh -L 5173:localhost:5173 -L 8000:localhost:8000 user@server`

### Issue: Wrong Permissions

**Test Button Result:**
```json
{
  "exists": true,
  "is_dir": true,
  "can_read": false  ← Can't read!
}
```

**Backend Log:**
```
Error accessing directory: Permission denied
```

**Solution:** Check file permissions on the server

## Advanced Debugging

### Check Backend is Running

```bash
curl http://localhost:8000/
# Should return JSON with server info
```

### Test Path Directly via API

```bash
curl "http://localhost:8000/api/test_path?path=/your/path/here"
# Returns detailed JSON about the path
```

### Check Server Info

```bash
curl http://localhost:8000/api/server_info
```

Returns:
```json
{
  "hostname": "hpc-server",
  "current_data_directory": "/current/path",
  "data_dir_exists": true,
  "current_working_directory": "/home/user/backend",
  "python_version": "3.11.5",
  "os_name": "posix"
}
```

## What to Share if You Need Help

If you're still having issues, share:

1. **Backend terminal output** (the detailed logs)
2. **Browser console output** (copy all the logs)
3. **Backend log file**: `cat backend/backend_debug.log`
4. **Test button result** for the path you're trying to use
5. **Server info**: `curl http://localhost:8000/api/server_info`

This will give complete visibility into what's happening!

