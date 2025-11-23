from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
import yt
import unyt
import os
from typing import List, Optional
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

@app.get("/")
def read_root():
    return {"message": "QUOKKA Viz Tool Backend"}

@app.get("/api/datasets")
def get_datasets():
    # Data directory is in the parent directory of the backend folder
    # Get the directory containing main.py
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to project root
    project_root = os.path.dirname(backend_dir)
    data_dir = os.path.join(project_root, "data")
    if not os.path.exists(data_dir):
        return {"datasets": []}
    
    datasets = [d for d in os.listdir(data_dir) if d.startswith("plt") and os.path.isdir(os.path.join(data_dir, d))]
    datasets.sort()
    return {"datasets": datasets}

@app.post("/api/load_dataset")
def load_dataset(filename: str = "plt00500"):
    global ds
    # Data directory is in the parent directory of the backend folder
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    path = os.path.join(project_root, "data", filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Dataset not found: {path}")
    
    try:
        ds = yt.load(path)
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
    global ds
    if ds is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
    
    # Load configuration
    config = load_config()
    SHORT_SIZE = config.get("short_size", 3.6)
    FONT_SIZE = config.get("font_size", 10)
    SCALE_BAR_HEIGHT_FRACTION = config.get("scale_bar_height_fraction", 15)
    # Note: dpi argument comes from request, but default_dpi in config could be used if we wanted to override the frontend's default?
    # The frontend sends a dpi value (defaulting to 300 or whatever is in state).
    # If we want to enforce config default_dpi when frontend sends 300 (which is its default), it's tricky.
    # But the user said "adjust DPI in the GUI". So GUI wins.
    # We just use config for the other params.

    # Debug logging
    import sys
    print(f"DEBUG: scale_bar_size={scale_bar_size}, scale_bar_unit={scale_bar_unit}, show_scale_bar={show_scale_bar}, dpi={dpi}")
    sys.stdout.flush()
    
    try:
        if coord is None:
            coord = ds.domain_center[ds.coordinates.axis_id[axis]]
        
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
        short_pixels = int(SHORT_SIZE * dpi)
        
        if aspect > 1:
            # Height > Width. Width is short side.
            nx = short_pixels
            ny = int(short_pixels * aspect)
            fig_width = SHORT_SIZE
            fig_height = SHORT_SIZE * aspect
        else:
            # Width > Height. Height is short side.
            ny = short_pixels
            nx = int(short_pixels / aspect)
            fig_height = SHORT_SIZE
            fig_width = SHORT_SIZE / aspect
            
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
            size_vertical_pixels = min(nx_pixels, ny_pixels) / SCALE_BAR_HEIGHT_FRACTION
            
            fontprops = fm.FontProperties(size=FONT_SIZE, weight='bold')
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
            
            if colorbar_orientation == 'top':
                cax = divider.append_axes("top", size="5%", pad=0.05)
                cbar = fig.colorbar(im, cax=cax, orientation="horizontal")
                cax.xaxis.set_ticks_position("top")
                cax.xaxis.set_label_position("top")
            else:
                # Default to right
                cax = divider.append_axes("right", size="5%", pad=0.05)
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
            cbar.ax.tick_params(labelsize=int(FONT_SIZE * 0.8))
            cbar.set_label(label, size=FONT_SIZE)
            
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
        
        return Response(content=buf.getvalue(), media_type="image/png")

    except Exception as e:
        print(f"Error generating slice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
