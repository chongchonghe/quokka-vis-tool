# Terminal Not Updating - Diagnosis

## The Problem

You're interacting with the browser, but the backend terminal shows **no output**. This means one of these issues:

## Scenario 1: Backend Not Running Where You Think

**Symptom:** Terminal is silent
**Cause:** The backend process died or you're looking at the wrong terminal

**Check:**
```bash
# Are you in the right terminal?
# Does it show uvicorn startup messages?
# Look for lines like:
#   INFO:     Uvicorn running on http://0.0.0.0:8000
#   INFO:     Application startup complete.

# If not, the backend might have crashed during startup
```

**Fix:**
1. Find the terminal where you ran `./start_backend_debug.sh`
2. Check if it shows "Application startup complete"
3. If it shows errors, share them
4. If it's blank/crashed, restart it

## Scenario 2: Wrong Port / SSH Tunnel Issue

**Symptom:** Browser connects but backend doesn't see requests
**Cause:** Frontend is connecting to a different backend (old one, or different port)

**Check:**
```bash
# On your Linux server, run:
./diagnose_connection.sh

# This will show:
# - What's listening on port 8000 (backend)
# - What's listening on port 5173/5174 (frontend)
# - Can you curl the backend?
```

**Common issue with SSH tunneling:**
- You have TWO backends running (one on server, one on laptop)
- Frontend connects to the laptop one instead of the server one
- Server backend never sees requests

## Scenario 3: Logging Disabled or Redirected

**Symptom:** Backend works but produces no output
**Cause:** Logging configuration issue

**Check:**
```bash
# Is the log file being created?
ls -la backend/backend_debug.log

# Watch it in real-time
tail -f backend/backend_debug.log

# Try to trigger a request, then check if file updates
```

## Scenario 4: Multiple Terminal Sessions

**Symptom:** Looking at old/wrong terminal
**Cause:** You have multiple terminals open and are watching the wrong one

**Check:**
1. How many terminals do you have open?
2. Which one shows the most recent timestamp?
3. Did you restart the backend and forget to look at the new terminal?

## What To Do Now

### Step 1: Verify Backend is Actually Running

On your **Linux server**, run:

```bash
cd /path/to/quokka-vis-tool

# Check if backend process exists
ps aux | grep uvicorn | grep -v grep

# Check if port 8000 is open
lsof -i :8000
# or
netstat -tlnp | grep 8000
```

**Expected output:**
```
python ... uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

If you see **nothing**, the backend is **NOT running**.

### Step 2: Check Backend Responds to Direct Requests

On the server, test the backend directly:

```bash
curl http://localhost:8000/
```

**Expected:** JSON response with server info
**If you get:** HTML with "Critical error" → Backend is crashing (share the error)
**If you get:** Connection refused → Backend not running

### Step 3: Check the Log File

```bash
# Go to backend directory
cd backend

# Check if log file exists and has recent content
ls -lah backend_debug.log

# Show last 50 lines
tail -50 backend_debug.log

# Watch it in real-time
tail -f backend_debug.log
```

Then in the browser, click "Test" again. **Does the log file update?**

- **YES**: Backend IS running, share the log content
- **NO**: Backend is either dead or logging is broken

### Step 4: Start Fresh with Maximum Verbosity

Stop everything and restart with explicit output:

```bash
# Kill any existing backend
pkill -f uvicorn

# Start backend with MAXIMUM verbosity
cd backend
source ../venv/bin/activate

# This will print EVERYTHING
python -u -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level trace 2>&1 | tee backend_full.log
```

The `-u` flag ensures unbuffered output (prints immediately).
The `tee` command saves output to a file AND shows it on screen.

Now try the browser again. You MUST see output.

### Step 5: Check What You're Actually Connecting To

In the browser console, check:

```javascript
// What URL is the frontend trying to reach?
console.log(window.location.origin);

// When you click Test, it tries:
// window.location.origin + '/api/test_path?path=...'
```

Is this the **same machine** where you started the backend?

## SSH Tunneling Specific Issues

If using SSH tunneling:

### Check Your SSH Tunnel

```bash
# On your local machine (Macbook), check SSH tunnel
ps aux | grep "ssh -L"

# You should see something like:
# ssh -L 5173:localhost:5173 -L 8000:localhost:8000 user@server
```

### Verify Port Forwarding

On your **local machine** (Macbook):

```bash
# This should reach the REMOTE backend
curl http://localhost:8000/
```

If this returns an error, your SSH tunnel is broken.

**Proper SSH tunnel command:**
```bash
ssh -L 5173:localhost:5173 -L 8000:localhost:8000 user@server.edu

# Keep this terminal open!
# Open browser on Macbook to http://localhost:5173
```

## Summary: Run These Commands

On your **Linux server** where backend should be running:

```bash
# 1. Check if backend is running
ps aux | grep uvicorn | grep -v grep

# 2. Test backend directly
curl http://localhost:8000/

# 3. Check logs
tail -50 backend/backend_debug.log

# 4. Run connection diagnosis
./diagnose_connection.sh
```

Share the output of all of these with me!

## Most Likely Issue

Based on "terminal not updating," the most likely cause is:

**The backend process crashed during startup** and you're looking at a dead terminal.

Look at the very end of the backend terminal output. Does it say:
- "Application startup complete" → Backend is running
- An error traceback → Backend crashed, share the error
- Nothing / blank → Terminal is dead, check with `ps aux | grep uvicorn`

