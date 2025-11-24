# SSH Tunnel Setup Guide

## The Problem You Had

Your SSH tunnel command was:
```bash
ssh -N -L 5173:localhost:5173 set2
```

This only tunnels the **frontend port (5173)**, but the frontend needs to talk to the **backend port (8000)** too!

## ✅ Correct SSH Tunnel Command

```bash
ssh -N -L 5173:localhost:5173 -L 8000:localhost:8000 set2
```

This tunnels:
- **5173**: Frontend (React/Vite dev server)
- **8000**: Backend (FastAPI Python server)

## Flags Explained

- `-N`: Don't execute remote commands (just forward ports)
- `-L 5173:localhost:5173`: Forward local port 5173 to remote port 5173
- `-L 8000:localhost:8000`: Forward local port 8000 to remote port 8000
- `set2`: Your SSH config alias for the server

## Alternative: Shorter Syntax

If your SSH config is set up, you can also use:

```bash
ssh -N -L 5173:localhost:5173 -L 8000:localhost:8000 user@server.edu
```

## Step-by-Step Setup

### On the Remote Server (set2):

1. **Start the backend:**
   ```bash
   cd /path/to/quokka-vis-tool
   ./start_backend_debug.sh
   ```
   
   Wait for: `INFO: Application startup complete.`

2. **Start the frontend (in another terminal):**
   ```bash
   cd /path/to/quokka-vis-tool/frontend
   npm run dev
   ```
   
   Wait for: `Local: http://localhost:5173/`

3. **Keep both terminals open and running!**

### On Your Local Macbook:

1. **Create the SSH tunnel:**
   ```bash
   ssh -N -L 5173:localhost:5173 -L 8000:localhost:8000 set2
   ```
   
   This terminal will appear to hang - **that's normal!** Keep it open.

2. **Test the tunnel (in a new terminal):**
   ```bash
   cd /path/to/quokka-vis-tool  # local copy
   ./test_ssh_tunnel.sh
   ```

3. **Open your browser:**
   ```
   http://localhost:5173
   ```

## How It Works

```
Your Browser (Macbook)
    ↓
http://localhost:5173 (local)
    ↓
[SSH Tunnel] ← Port forwarding
    ↓
http://localhost:5173 (remote server)
    ↓
Vite Dev Server (on server)
    ↓
Proxies API requests to localhost:8000 (on server)
    ↓
[SSH Tunnel] ← Port forwarding for API calls
    ↓
http://localhost:8000 (local)
    ↓
FastAPI Backend (on server)
```

## Testing the Tunnel

### Quick Test

On your **local Macbook** (after starting tunnel):

```bash
# Test backend
curl http://localhost:8000/
# Expected: JSON with server info

# Test frontend
curl http://localhost:5173/
# Expected: HTML
```

### Full Test

Run the test script:
```bash
./test_ssh_tunnel.sh
```

## Troubleshooting

### "Connection refused" on port 8000

**Problem:** You forgot to tunnel port 8000
**Fix:** Add `-L 8000:localhost:8000` to your SSH command

### "Connection refused" on port 5173

**Problem:** Frontend not running on server
**Fix:** Start `npm run dev` on the server

### Terminal shows "Failed to set data directory"

**Problem:** This was your original issue!
**Cause:** You were only tunneling port 5173, so the frontend couldn't reach the backend

**Fix:** Use the correct tunnel command with both ports

### SSH tunnel keeps disconnecting

**Problem:** Network timeout
**Fix:** Add keep-alive to your SSH config:

```bash
# Add to ~/.ssh/config on your Macbook
Host set2
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### Multiple backends running

**Problem:** You have a backend running on your Macbook AND on the server
**Solution:** Kill the local one:

```bash
# On Macbook
pkill -f uvicorn
```

## Advanced: SSH Config Method

Edit `~/.ssh/config` on your Macbook:

```
Host set2-tunnel
    HostName your.server.edu
    User yourname
    LocalForward 5173 localhost:5173
    LocalForward 8000 localhost:8000
    ServerAliveInterval 60
```

Then simply run:
```bash
ssh -N set2-tunnel
```

## Verification Checklist

✅ Backend running on server (check with `ps aux | grep uvicorn`)
✅ Frontend running on server (check with `ps aux | grep vite`)  
✅ SSH tunnel running on Macbook (check with `ps aux | grep "ssh -N"`)
✅ Can curl http://localhost:8000/ on Macbook
✅ Can curl http://localhost:5173/ on Macbook
✅ Browser opens to http://localhost:5173
✅ UI shows server hostname from remote server
✅ Test button works and shows path info

## One-Liner for Easy Access

Add this to your shell profile on Macbook:

```bash
alias tunnel-vis='ssh -N -L 5173:localhost:5173 -L 8000:localhost:8000 set2'
```

Then just run:
```bash
tunnel-vis
```

## Summary

**Wrong (what you had):**
```bash
ssh -N -L 5173:localhost:5173 set2  # Missing port 8000!
```

**Correct:**
```bash
ssh -N -L 5173:localhost:5173 -L 8000:localhost:8000 set2
```

That's it! Now your frontend can talk to your backend through the tunnel.

