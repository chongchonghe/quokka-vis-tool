# QUOKKA Viz Tool

A high-performance, browser-based visualization tool for 3D astrophysical simulation data (BoxLib format). Built with a **FastAPI** backend (using `yt`) and a **React** frontend.

## Features

- **Interactive Slicing:** View 2D slices of 3D datasets along X, Y, or Z axes.
- **Dynamic Controls:** Adjust field, colormap, log scale, and min/max limits in real-time.
- **Animation:** Play through datasets (time series) with adjustable FPS.
- **Customizable Output:**
  - Configurable figure size, font size, and DPI.
  - Toggleable scale bar and colorbar (always on the right).
  - Adjustable colorbar width and scale bar height.
- **Performance:** Backend image caching for smooth playback of repeated frames.

## Project Structure

```
vis-tool-3d/
├── backend/          # Python FastAPI server
│   ├── main.py       # API endpoints and image generation
│   └── config.yaml   # Configuration (font size, DPI, cache size, etc.)
├── frontend/         # React application
│   ├── src/          # Source code (components, App.jsx)
│   └── ...
├── data/             # Directory for simulation datasets (plt*)
└── requirements.txt  # Python dependencies
```

## Setup & Installation

### Prerequisites
- Python 3.8+
- Node.js & npm

### 1. Backend Setup

1.  Navigate to the project root.
2.  Create and activate a virtual environment via venv or uv and activate it.
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Start the server:
    ```bash
    cd backend
    uvicorn main:app --reload
    ```
    The backend runs on `http://localhost:8000`.

### 2. Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
    The app will be accessible at `http://localhost:5173`.

## Quick Start Scripts (Recommended)

For easier workflow, use the provided startup scripts:

### Basic Usage

```bash
# Start both services (runs in background with logs)
./start.sh

# Check status
./status.sh

# Stop all services
./stop.sh

# Development mode (runs in foreground with live logs)
./dev.sh
```

### What the scripts do:
- **`start.sh`**: Starts both backend and frontend in the background
  - Automatically loads Python venv (assumes npm is available via `.bashrc`)
  - Logs saved to `~/scripts/logs/quokka-vis-tool/`
  - Can be run from any directory
  - Press Ctrl+C or run `./stop.sh` to stop

- **`stop.sh`**: Stops all running services

- **`status.sh`**: Shows current status and connectivity

- **`dev.sh`**: Development mode with live logs and auto-reload

See [SCRIPTS.md](SCRIPTS.md) for detailed usage and troubleshooting.

## Remote Access (SSH Tunneling)

To access the visualization tool from a remote machine (e.g., your laptop) while the server runs on an HPC cluster or workstation:

### Setup Instructions

1.  **Start the backend on the remote server:**
    ```bash
    # On the HPC server (here on setonix)
    cd /home/chongchong/softwares-setonix/quokka-vis-tool/backend
    source ~/softwares-setonix/python-envs/uv-quokka-vis-tool/bin/activate
    uvicorn main:app --host 0.0.0.0 --port 9010
    ```

2.  **Start the frontend on the remote server:**
    ```bash
    # On the HPC server / remote workstation (in a separate terminal)
    # Note: On Setonix, nvm should be loaded via .bashrc in login shells
    cd /home/chongchong/softwares-setonix/quokka-vis-tool/frontend
    npm run dev
    ```

3.  **Create an SSH tunnel from your local machine:**
    ```bash
    # On your local laptop/desktop
    ssh -L 5173:localhost:5173 -L 9010:localhost:9010 user@remote_host
    ```
    Or if you only want to tunnel the frontend (recommended):
    ```bash
    ssh -L 5173:localhost:5173 user@remote_host
    ```

4.  **Open your browser** on your local machine to `http://localhost:5173`.

### Important Notes for SSH Tunneling

**⚠️ Data Directory Path:**
- The **data directory path must exist on the HPC server**, not on your local machine
- When you set the data directory in the web interface, enter a path that exists on the **remote server's filesystem**
- Example: If your data is at `/scratch/username/simulations/` on the HPC server, enter that path (not a local path like `/Users/...` or `C:\...`)
- The UI will display the backend server's hostname to help you identify which machine to use

**How it works:**
- The frontend (web interface) runs in your browser on your local machine
- The backend (Python server) runs on the remote HPC server where your data is located
- SSH tunneling connects them securely through the tunnel

The frontend (port 5173) will proxy API requests to the backend automatically. You can tunnel both ports or just port 5173 (the backend will be accessed via the proxy).

**⚠️ Important Port Configuration:**
- If you use a port other than 8000 for the backend (e.g., port 9010), you **must** update `frontend/vite.config.js`
- Change the proxy target to match your backend port:
  ```javascript
  proxy: {
    '/api': {
      target: 'http://localhost:9010',  // Match your backend port
      changeOrigin: true,
    },
  },
  ```
- After changing the config, restart the frontend development server (`npm run dev`)

## Configuration

Modify `backend/config.yaml` to customize the visualization appearance and performance:

```yaml
short_size: 3.6               # Figure short dimension in inches
font_size: 20                 # Base font size for labels
scale_bar_height_fraction: 15 # Scale bar height (1/N of short axis)
colormap_fraction: 0.1        # Colorbar width fraction
default_dpi: 300              # Output resolution
cache_max_size: 32            # Number of images to cache in memory
```

## Usage

1.  Place your BoxLib datasets (folders starting with `plt`) in the `data/` directory at the project root.
2.  Open the web interface.
3.  Select a dataset and field to visualize.
4.  Use the controls to slice, animate, and adjust the view.

## Workflow Tips & Optimizations

### For Remote Development on HPC

1. **Use tmux or screen** for persistent sessions:
   ```bash
   # Start a tmux session
   tmux new -s quokka-viz
   
   # Run the visualization tool
   ./start.sh
   
   # Detach: Press Ctrl+b then d
   # Reattach later: tmux attach -t quokka-viz
   ```

2. **SSH config for easier tunneling** (`~/.ssh/config` on your local machine):
   ```
   Host setonix
       HostName setonix.pawsey.org.au
       User your_username
       LocalForward 5173 localhost:5173
       LocalForward 9010 localhost:9010
			 SessionType none
   ```
   Then simply: `ssh setonix`

3. **Quick restart after code changes**:
   ```bash
   ./stop.sh && ./start.sh
   ```
   Or use `./dev.sh` for auto-reload during development

4. **Monitor logs in real-time**:
   ```bash
   tail -f logs/backend.log logs/frontend.log
   ```

5. **Debugging**: Use `./dev.sh` instead of `./start.sh` to see live logs with color-coded output

### Performance Tips

- Increase `cache_max_size` in `backend/config.yaml` if you have lots of RAM
- Lower `default_dpi` for faster rendering during exploration, increase for publication
- Use the log scale toggle for fields with large dynamic range
- The backend caches rendered images, so re-viewing the same slice is instant
