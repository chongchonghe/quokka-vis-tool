# URGENT: Backend Crashing - How to Fix

## The Problem

Your backend is **crashing** on every request. The browser shows:
```
Critical error while processing request: /api/test_path
500 INTERNAL SERVER ERROR
```

This means:
- ✓ Backend IS running
- ✓ Frontend CAN connect to it
- ✗ Backend CRASHES when processing requests

## Step 1: Check Backend Terminal **RIGHT NOW**

Look at your backend terminal. You should see Python error tracebacks that look like:

```
Traceback (most recent call last):
  File "...", line XXX, in <module>
    ...
SomeError: error message here
```

**CRITICAL**: **Share the complete error traceback** from the backend terminal. This will tell us exactly what's crashing.

## Step 2: Quick Backend Test

Run this to see if the backend module can even load:

```bash
cd /Users/cche/git/vis-tool-3d
python3 test_backend_direct.py
```

This will test:
- Can Python import all required modules?
- Can the backend file load?
- Are there any syntax errors?

## Step 3: Check Backend Logs

```bash
cat backend/backend_debug.log
```

Or watch in real-time:
```bash
tail -f backend/backend_debug.log
```

## Common Causes of Backend Crashes

### 1. Missing `config.yaml`

**Error looks like:**
```
FileNotFoundError: [Errno 2] No such file or directory: '.../backend/config.yaml'
```

**Fix:**
```bash
cd backend
cat > config.yaml << 'EOF'
short_size: 3.6
font_size: 10
scale_bar_height_fraction: 15
default_dpi: 300
cache_max_size: 32
colormap_fraction: 0.1
EOF
```

### 2. Missing Dependencies

**Error looks like:**
```
ModuleNotFoundError: No module named 'yt'
```

**Fix:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Syntax Error in Code

**Error looks like:**
```
SyntaxError: invalid syntax
```

**This means the recent code changes have a bug.**

### 4. Import Error

**Error looks like:**
```
ImportError: cannot import name '...'
```

**Fix:** Check the imports at the top of `backend/main.py`

## Step 4: Start Backend with Maximum Verbosity

Stop your current backend (Ctrl+C) and restart with full debug:

```bash
cd backend
source ../venv/bin/activate

# Start with maximum logging
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

Watch for ANY errors during startup.

## Step 5: Test Individual Endpoints

Once backend starts (even if crashing on requests), test from command line:

```bash
# Test 1: Root endpoint
curl http://localhost:8000/

# Test 2: Server info
curl http://localhost:8000/api/server_info

# Test 3: Test path
curl "http://localhost:8000/api/test_path?path=/tmp"
```

If these return HTML errors, look at backend terminal for the Python traceback.

## What To Share

To get help, share:

1. **Complete backend terminal output** from when it starts until the first error
2. **Output of:** `python3 test_backend_direct.py`
3. **Output of:** `cat backend/backend_debug.log | tail -100`
4. **Output of:** `curl http://localhost:8000/`

## Quick Rollback

If the backend was working before I added debug features, you can rollback:

```bash
cd /Users/cche/git/vis-tool-3d
git diff backend/main.py > debug_changes.patch
git checkout backend/main.py  # Restore original
```

Then restart backend and see if it works.

## Most Likely Issue

Based on the error pattern, the most likely causes (in order):

1. **Missing `config.yaml` file** - The `load_config()` function is trying to read it
2. **Syntax error** in the recent code changes
3. **Import error** - something can't be imported
4. **Environment issue** - wrong Python version or virtual environment

**Check the backend terminal output - it will tell you exactly which one!**

