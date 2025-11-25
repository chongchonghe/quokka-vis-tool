# QUOKKA Viz Tool - Script Usage Guide

Quick reference for the startup scripts.

## Scripts Overview

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `start.sh` | Start services in background | Normal usage, long-running sessions |
| `stop.sh` | Stop all services | Cleanup, restart |
| `status.sh` | Check service status | Troubleshooting |
| `dev.sh` | Development mode with live logs | Development, debugging |

## Usage Examples

### Basic Workflow

```bash
# Start everything (from any directory)
~/softwares-setonix/quokka-vis-tool/start.sh

# Or if you're in the project directory
./start.sh

# Check if everything is running
./status.sh

# When done
./stop.sh
```

### With tmux (Recommended for Remote Sessions)

```bash
# Create a new tmux session
tmux new -s viz

# Start the tool
~/softwares-setonix/quokka-vis-tool/start.sh

# Detach: Ctrl+b, then d
# Your services keep running!

# Later, reattach
tmux attach -t viz
```

### Development Mode

```bash
# Run with live logs for debugging
./dev.sh

# You'll see colored output from both services
# Auto-reload is enabled
# Press Ctrl+C to stop
```

## Log Files

All logs are stored in: `~/scripts/logs/quokka-vis-tool/`

- `backend.log` - Python/FastAPI backend logs
- `frontend.log` - Vite/React frontend logs

View logs in real-time:
```bash
tail -f ~/scripts/logs/quokka-vis-tool/backend.log
tail -f ~/scripts/logs/quokka-vis-tool/frontend.log
```

## Customization

To change ports or paths, edit the variables at the top of each script:

```bash
# In start.sh
BACKEND_PORT=9010
VENV_PATH="$HOME/softwares-setonix/python-envs/uv-quokka-vis-tool"
LOG_DIR="$HOME/scripts/logs/quokka-vis-tool"
```

**Important:** If you change `BACKEND_PORT`, also update `frontend/vite.config.js` to match.

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the ports
lsof -i :9010
lsof -i :5173

# Stop everything
./stop.sh
```

### Services Won't Start
```bash
# Check logs
cat ~/scripts/logs/quokka-vis-tool/backend.log
cat ~/scripts/logs/quokka-vis-tool/frontend.log

# Verify npm is available
which npm
npm --version

# Verify venv exists
ls ~/softwares-setonix/python-envs/uv-quokka-vis-tool/
```

### npm Not Found
The scripts expect npm to be available from your shell (loaded via `.bashrc`). If you get "npm not found":
- Make sure nvm is properly configured in your `.bashrc`
- Run in a login shell: `bash -l start.sh`
- Or manually source nvm before running the script

