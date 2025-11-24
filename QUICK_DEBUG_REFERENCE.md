# Quick Debug Reference Card

## 🚀 Quick Start

```bash
# Terminal 1: Start backend with debug logging
./start_backend_debug.sh

# Terminal 2: Start frontend  
cd frontend && npm run dev

# Browser: Open http://localhost:5173 and press F12 for console
```

## 🔍 Where to Look

| Problem | Check Here |
|---------|-----------|
| "Failed to set data directory" | Backend terminal + browser console |
| Path doesn't exist | Backend logs show `os.path.exists() = False` |
| Wrong server | Check hostname in UI and logs |
| Network issues | Browser console shows "Failed to fetch" |
| Permission issues | Backend logs show "can_read = False" |

## 🛠️ Debug Tools

### 1. Test Button
**Before setting a path:**
- Enter path in field
- Click **"Test"** 
- Read the JSON result
- Verify `exists: true` and `is_dir: true`

### 2. Backend Logs
**Watch in real-time:**
```bash
tail -f backend/backend_debug.log
```

### 3. Browser Console
**See all frontend activity:**
- Press `F12` (or `Cmd+Option+I` on Mac)
- Go to "Console" tab
- All requests logged with `========` separators

### 4. Test Path API
**Direct test from command line:**
```bash
curl "http://localhost:8000/api/test_path?path=/your/path/here"
```

### 5. Server Info API
**Check backend status:**
```bash
curl http://localhost:8000/api/server_info
```

## 📋 What Gets Logged

### Backend Terminal
```
====== Incoming Request ======
Method: POST
URL: http://localhost:8000/api/set_data_dir
Body: {"path":"/your/path"}
================================================================================
SET_DATA_DIR endpoint called
Backend server hostname: hpc-login-01
Attempting to set data directory to: /your/path
os.path.exists(/your/path) = True
os.path.isdir(/your/path) = True
Successfully changed DATA_DIR
================================================================================
```

### Browser Console
```
========================================
handleSetDataDir called
dataDir value: /your/path
Request body: {path: "/your/path"}
Response status: 200
Success response data: {message: "...", path: "..."}
========================================
```

## 🐛 Common Issues

### Issue: "Directory not found"

**What you'll see:**
```
Backend log: Path does not exist: /Users/cche/data
Browser: Error: Directory not found on server 'hpc-login-01'
```

**Cause:** Using local machine path instead of server path

**Fix:** Use server path like `/scratch/username/data`

---

### Issue: "Failed to fetch"

**What you'll see:**
```
Browser: TypeError: Failed to fetch
Browser: net::ERR_CONNECTION_REFUSED
```

**Cause:** Backend not running or SSH tunnel broken

**Fix:** 
- Check backend: `curl http://localhost:8000/`
- Restart SSH tunnel: `ssh -L 5173:localhost:5173 -L 8000:localhost:8000 user@server`

---

### Issue: "Path is not a directory"

**What you'll see:**
```
Backend log: os.path.isdir(/your/path) = False
```

**Cause:** Path points to a file, not a directory

**Fix:** Check the path, it should point to a folder

---

### Issue: Permission denied

**What you'll see:**
```
Backend log: os.access(/your/path, os.R_OK) = False
Backend log: Error accessing directory: Permission denied
```

**Cause:** No read permission on the directory

**Fix:** 
```bash
# On the server
chmod +r /your/path
# or
chmod 755 /your/path
```

## 💡 Pro Tips

1. **Always use the Test button first** - saves time!

2. **Watch both logs simultaneously:**
   ```bash
   # Terminal 1: Backend
   ./start_backend_debug.sh
   
   # Terminal 2: Watch log file
   tail -f backend/backend_debug.log
   ```

3. **Copy/paste server hostname** from UI into your path

4. **Use tab completion** on the server to verify paths:
   ```bash
   ssh user@hpc-server
   ls -la /scratch/username/data/   # Verify path exists
   ```

5. **Save console logs:** Right-click in browser console → "Save as..."

## 📞 Getting Help

If still stuck, share these:

1. **Backend terminal output** (copy the relevant section)
2. **Browser console output** (copy all between `========`)
3. **Test button result** (the JSON popup)
4. **Server info:**
   ```bash
   curl http://localhost:8000/api/server_info
   ```
5. **Backend log file:**
   ```bash
   tail -100 backend/backend_debug.log
   ```

## 🎯 Success Checklist

- [ ] Backend running (terminal shows startup message)
- [ ] Frontend running (browser opens to app)
- [ ] Browser console open (F12)
- [ ] Server hostname visible in UI
- [ ] Test button works (shows JSON)
- [ ] Test shows `exists: true` and `is_dir: true`
- [ ] Set button works (success message)
- [ ] Backend logs show success
- [ ] Datasets appear in the list

If all checked = You're good to go! ✅

