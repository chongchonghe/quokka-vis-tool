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
│   ├── config.yaml   # Configuration (font size, DPI, cache size, etc.)
│   └── utils.py      # Utility functions
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
2.  Create and activate a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
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
