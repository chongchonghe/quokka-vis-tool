from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
import yt
import unyt
import os
from typing import List, Optional
from functools import lru_cache
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import yaml
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm

from fastapi.middleware.cors import CORSMiddleware


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# Initial load to set defaults if needed, or just rely on load_config in endpoints
# We can keep defaults as fallback
DEFAULT_CONFIG = {
    "short_size": 3.6,
    "font_size": 10,
    "scale_bar_height_fraction": 15,
    "default_dpi": 300
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. In prod, specify frontend URL.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to hold the loaded dataset
ds = None
current_dataset_path = None

# Default data directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
DATA_DIR = os.path.join(project_root, "data")

from pydantic import BaseModel

class DataDirRequest(BaseModel):
    path: str

@app.get("/")
def read_root():
    return {"message": "QUOKKA Viz Tool Backend"}

@app.post("/api/set_data_dir")
def set_data_dir(request: DataDirRequest):
    global DATA_DIR
    path = request.path
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")
    
    DATA_DIR = path
    return {"message": f"Data directory set to: {DATA_DIR}", "path": DATA_DIR}

@app.get("/api/datasets")
def get_datasets():
    global DATA_DIR
    if not os.path.exists(DATA_DIR):
        return {"datasets": []}
    
    datasets = [d for d in os.listdir(DATA_DIR) if d.startswith("plt") and os.path.isdir(os.path.join(DATA_DIR, d))]
    datasets.sort()
    return {"datasets": datasets}

@app.post("/api/load_dataset")
def load_dataset(filename: str = "plt00500"):
    global ds, DATA_DIR
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Dataset not found: {path}")
    
    try:
        ds = yt.load(path)
        global current_dataset_path
        current_dataset_path = path
        return {"message": f"Dataset loaded: {path}", "domain_dimensions": ds.domain_dimensions.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fields")
def get_fields():
    global ds
    if ds is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
    
    # Return a list of fluid fields
    # ds.field_list is a list of tuples (field_type, field_name)
    # We only want the field_name for boxlib fields
    fields = [f[1] for f in ds.field_list if f[0] == 'boxlib']
    return {"fields": fields}


# Load config for cache size
try:
    _config = load_config()
    CACHE_MAX_SIZE = _config.get("cache_max_size", 32)
except Exception:
    CACHE_MAX_SIZE = 32

@lru_cache(maxsize=CACHE_MAX_SIZE)
def _generate_slice_image(
    dataset_path: str,
    axis: str,
    field: str,
    coord: float,
    vmin: Optional[float],
    vmax: Optional[float],
    show_colorbar: bool,
    log_scale: bool,
    colorbar_label: Optional[str],
    colorbar_orientation: str,
    cmap: str,
    dpi: int,
    show_scale_bar: bool,
    scale_bar_size: Optional[float],
    scale_bar_unit: Optional[str],
    short_size: float,
    font_size: int,
    scale_bar_height_fraction: float,
    colormap_fraction: float
):
    # Ensure global ds matches dataset_path
    # In a single-threaded async environment, this should be consistent if load_dataset was called.
    # However, if multiple requests interleave, ds might have changed.
    # But since we are caching based on dataset_path, if ds doesn't match, we might be in trouble.
    # Ideally we would load ds here if needed, but that's slow.
    # We assume the caller (get_slice) ensures ds is loaded and matches dataset_path.
    # Or we can check:
    global ds
    if ds is None or current_dataset_path != dataset_path:
        # This might happen if server restarted or race condition (unlikely with uvicorn default)
        # We try to reload if path exists
        if os.path.exists(dataset_path):
            ds = yt.load(dataset_path)
        else:
            raise Exception(f"Dataset not found or mismatch: {dataset_path}")

    slc = yt.SlicePlot(ds, axis, ("boxlib", field), center=ds.domain_center)
    
    # Calculate aspect ratio
    axis_id = ds.coordinates.axis_id[axis]
    x_ax_id = ds.coordinates.x_axis[axis_id]
    y_ax_id = ds.coordinates.y_axis[axis_id]
    
    Wx = ds.domain_width[x_ax_id].v
    Wy = ds.domain_width[y_ax_id].v
    aspect = float(Wy / Wx)
    
    # Calculate resolution (nx, ny) based on SHORT_SIZE and DPI
    # SHORT_SIZE is in inches.
    short_pixels = int(short_size * dpi)
    if aspect > 1:
        # Height > Width. Width is short side.
        nx = short_pixels
        ny = int(short_pixels * aspect)
        fig_width = short_size
        fig_height = short_size * aspect
    else:
        # Width > Height. Height is short side.
        ny = short_pixels
        nx = int(short_pixels / aspect)
        fig_height = short_size
        fig_width = short_size / aspect

        
    slc.set_buff_size((nx, ny))
    
    frb = slc.frb
    image_data = np.array(frb[("boxlib", field)])
    
    buf = io.BytesIO()
    
    # Common scale bar logic
    def add_scale_bar(ax, nx_pixels, ny_pixels):
        # Get axis information
        axis_id = ds.coordinates.axis_id[axis]
        x_ax_id = ds.coordinates.x_axis[axis_id]
        domain_width = ds.domain_width[x_ax_id]
        
        # Use custom scale bar size if provided, otherwise auto-calculate
        if scale_bar_size is not None and scale_bar_unit is not None:
            try:
                custom_quantity = yt.YTQuantity(scale_bar_size, scale_bar_unit)
                box_length_fraction = float(custom_quantity / domain_width)
                display_label = f'{scale_bar_size:.3g} {scale_bar_unit}'
            except Exception as e:
                print(f"Warning: Could not convert {scale_bar_size} {scale_bar_unit}: {e}")
                box_length_fraction = 0.2
                display_label = f'{0.2 * float(domain_width.v):.3g} {domain_width.units}'
        else:
            box_length_fraction = 0.2
            scale_value = 0.2 * float(domain_width.v)
            magnitude = 10 ** np.floor(np.log10(scale_value))
            nice_scale = np.round(scale_value / magnitude) * magnitude
            box_length_fraction = nice_scale / float(domain_width.v)
            display_label = f'{nice_scale:.3g} {domain_width.units}'
        
        scale_bar_pixels = box_length_fraction * nx_pixels
        
        # Calculate size_vertical (height of scale bar)
        # We want height = SHORT_SIZE / SCALE_BAR_HEIGHT_FRACTION (inches)
        # We know min(nx, ny) corresponds to SHORT_SIZE (inches)
        # So size_vertical_pixels = min(nx, ny) / SCALE_BAR_HEIGHT_FRACTION
        size_vertical_pixels = min(nx_pixels, ny_pixels) / scale_bar_height_fraction
        
        fontprops = fm.FontProperties(size=font_size, weight='bold')
        scalebar = AnchoredSizeBar(
            ax.transData,
            scale_bar_pixels,
            display_label,
            'lower left',
            pad=0.5,
            color='white',
            frameon=False,
            size_vertical=size_vertical_pixels,
            fontproperties=fontprops
        )
        ax.add_artist(scalebar)

    if show_colorbar:
        # Use matplotlib figure to show colorbar
        fig = plt.figure(figsize=(fig_width, fig_height))
        ax = fig.add_subplot(111)
        
        norm = matplotlib.colors.LogNorm(vmin=vmin, vmax=vmax) if log_scale else matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        
        im = ax.imshow(image_data, origin='lower', cmap=cmap, norm=norm)
        
        # Create divider for existing axes instance
        divider = make_axes_locatable(ax)
        
        # Colorbar always on the right
        # Width is 1/SCALE_BAR_HEIGHT_FRACTION of the short axis (SHORT_SIZE)
        cbar_width_inches = short_size / scale_bar_height_fraction
        cax = divider.append_axes("right", size=cbar_width_inches, pad=0.05)
        cbar = fig.colorbar(im, cax=cax, orientation="vertical")
        
        # Set colorbar label
        if colorbar_label:
            label = colorbar_label
        else:
            try:
                label = ds.field_info[("boxlib", field)].get_label()
            except:
                label = field
        
        # Set font size for colorbar (ticks at 80% of FONT_SIZE)
        cbar.ax.tick_params(labelsize=int(font_size * 0.8))
        cbar.set_label(label, size=font_size)
        
        if show_scale_bar:
            add_scale_bar(ax, nx, ny)
        
        ax.axis('off')
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=dpi)
        plt.close(fig)
    else:
        if show_scale_bar:
            fig = plt.figure(figsize=(fig_width, fig_height))
            ax = fig.add_subplot(111)
            
            norm = matplotlib.colors.LogNorm(vmin=vmin, vmax=vmax) if log_scale else matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
            im = ax.imshow(image_data, origin='lower', cmap=cmap, norm=norm)
            
            add_scale_bar(ax, nx, ny)
            
            ax.axis('off')
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=dpi)
            plt.close(fig)
        else:
            # Use imsave for pure data view, but we need to apply log scale and colormap manually
            norm = matplotlib.colors.LogNorm(vmin=vmin, vmax=vmax) if log_scale else matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
            mapped_data = norm(image_data)
            cm = matplotlib.colormaps[cmap]
            colored_data = cm(mapped_data)
            
            # We can use plt.imsave
            plt.imsave(buf, colored_data, origin='lower', format='png', dpi=dpi)
        
    buf.seek(0)
    return buf.getvalue()

@app.get("/api/slice")
def get_slice(
    axis: str = "z", 
    field: str = "density", 
    coord: Optional[float] = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    show_colorbar: bool = False,
    log_scale: bool = True,
    colorbar_label: Optional[str] = None,
    colorbar_orientation: str = "right",
    cmap: str = "viridis",
    dpi: int = 300,
    show_scale_bar: bool = False,
    scale_bar_size: Optional[float] = None,
    scale_bar_unit: Optional[str] = None
):
    global ds, current_dataset_path
    if ds is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
    
    # Load configuration
    config = load_config()
    SHORT_SIZE = config.get("short_size", 3.6)
    FONT_SIZE = config.get("font_size", 10)
    SCALE_BAR_HEIGHT_FRACTION = config.get("scale_bar_height_fraction", 15)
    COLORMAP_FRACTION = config.get("colormap_fraction", 0.1)

    # Debug logging
    import sys
    print(f"DEBUG: scale_bar_size={scale_bar_size}, scale_bar_unit={scale_bar_unit}, show_scale_bar={show_scale_bar}, dpi={dpi}")
    sys.stdout.flush()
    
    try:
        if coord is None:
            coord = ds.domain_center[ds.coordinates.axis_id[axis]]
            # Convert to float to ensure it's hashable and consistent
            coord = float(coord)
        
        image_bytes = _generate_slice_image(
            current_dataset_path,
            axis,
            field,
            coord,
            vmin,
            vmax,
            show_colorbar,
            log_scale,
            colorbar_label,
            colorbar_orientation,
            cmap,
            dpi,
            show_scale_bar,
            scale_bar_size,
            scale_bar_unit,
            SHORT_SIZE,
            FONT_SIZE,
            SCALE_BAR_HEIGHT_FRACTION,
            COLORMAP_FRACTION
        )
        
        return Response(content=image_bytes, media_type="image/png")

    except Exception as e:
        print(f"Error generating slice: {e}")
        # If error occurs, we might want to clear cache for this key? 
        # But lru_cache doesn't support clearing specific key easily.
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
