from fastapi import FastAPI, HTTPException, Query, Request
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
import logging
import sys
import traceback
import socket

from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backend_debug.log')
    ]
)
logger = logging.getLogger(__name__)


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

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"====== Incoming Request ======")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Client: {request.client}")
    
    # Read body for POST requests
    if request.method == "POST":
        body = await request.body()
        logger.info(f"Body: {body.decode('utf-8') if body else 'Empty'}")
        # Store body for later use
        request._body = body
    
    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code}")
    logger.info(f"====== Request Complete ======\n")
    return response

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
    hostname = socket.gethostname()
    cwd = os.getcwd()
    return {
        "message": "QUOKKA Viz Tool Backend",
        "server_hostname": hostname,
        "current_working_directory": cwd,
        "current_data_directory": DATA_DIR
    }

@app.post("/api/set_data_dir")
def set_data_dir(request: DataDirRequest):
    global DATA_DIR
    
    logger.info("=" * 80)
    logger.info("SET_DATA_DIR endpoint called")
    logger.info(f"Received request object: {request}")
    logger.info(f"Request path value: {request.path}")
    logger.info(f"Request path type: {type(request.path)}")
    
    hostname = socket.gethostname()
    logger.info(f"Backend server hostname: {hostname}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Current DATA_DIR value: {DATA_DIR}")
    
    path = request.path
    logger.info(f"Attempting to set data directory to: {path}")
    
    # Check if path is absolute
    if not os.path.isabs(path):
        logger.warning(f"Path is not absolute: {path}")
        abs_path = os.path.abspath(path)
        logger.info(f"Converting to absolute path: {abs_path}")
        path = abs_path
    
    # Check if path exists
    logger.info(f"Checking if path exists: {path}")
    path_exists = os.path.exists(path)
    logger.info(f"os.path.exists({path}) = {path_exists}")
    
    if not path_exists:
        # List parent directory to help debug
        parent_dir = os.path.dirname(path)
        logger.error(f"Path does not exist: {path}")
        logger.info(f"Parent directory: {parent_dir}")
        
        if os.path.exists(parent_dir):
            try:
                contents = os.listdir(parent_dir)
                logger.info(f"Parent directory contents: {contents[:20]}")  # First 20 items
            except Exception as e:
                logger.error(f"Could not list parent directory: {e}")
        else:
            logger.error(f"Parent directory also does not exist: {parent_dir}")
        
        error_msg = f"Directory not found on server '{hostname}': {path}\n\nNote: When using SSH tunneling, the path must exist on the machine where the backend is running, not your local machine."
        logger.error(f"Raising HTTPException 404: {error_msg}")
        raise HTTPException(status_code=404, detail=error_msg)
    
    # Check if it's a directory
    logger.info(f"Checking if path is a directory: {path}")
    is_directory = os.path.isdir(path)
    logger.info(f"os.path.isdir({path}) = {is_directory}")
    
    if not is_directory:
        error_msg = f"Path is not a directory on server '{hostname}': {path}"
        logger.error(f"Raising HTTPException 400: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check permissions
    try:
        logger.info(f"Checking read permissions for: {path}")
        can_read = os.access(path, os.R_OK)
        logger.info(f"os.access({path}, os.R_OK) = {can_read}")
        
        # Try to list directory
        contents = os.listdir(path)
        logger.info(f"Successfully listed directory, found {len(contents)} items")
        logger.info(f"First 10 items: {contents[:10]}")
    except Exception as e:
        logger.error(f"Error accessing directory: {e}")
        logger.error(traceback.format_exc())
    
    # Set the directory
    old_data_dir = DATA_DIR
    DATA_DIR = path
    logger.info(f"Successfully changed DATA_DIR from '{old_data_dir}' to '{DATA_DIR}'")
    
    response = {
        "message": f"Data directory set to: {DATA_DIR} on server '{hostname}'",
        "path": DATA_DIR,
        "server": hostname
    }
    logger.info(f"Returning success response: {response}")
    logger.info("=" * 80 + "\n")
    
    return response

@app.get("/api/server_info")
def get_server_info():
    hostname = socket.gethostname()
    info = {
        "hostname": hostname,
        "current_data_directory": DATA_DIR,
        "data_dir_exists": os.path.exists(DATA_DIR),
        "current_working_directory": os.getcwd(),
        "backend_file_location": os.path.abspath(__file__),
        "python_version": sys.version,
        "os_name": os.name,
        "can_read_data_dir": os.access(DATA_DIR, os.R_OK) if os.path.exists(DATA_DIR) else False
    }
    
    logger.info("Server info requested:")
    logger.info(f"  Hostname: {hostname}")
    logger.info(f"  Current DATA_DIR: {DATA_DIR}")
    logger.info(f"  DATA_DIR exists: {info['data_dir_exists']}")
    
    return info

@app.get("/api/test_path")
def test_path(path: str):
    """Test endpoint to check if a path exists and get detailed info"""
    logger.info(f"Testing path: {path}")
    
    result = {
        "path": path,
        "is_absolute": os.path.isabs(path),
        "exists": os.path.exists(path),
        "is_dir": os.path.isdir(path) if os.path.exists(path) else None,
        "is_file": os.path.isfile(path) if os.path.exists(path) else None,
        "can_read": os.access(path, os.R_OK) if os.path.exists(path) else None,
        "absolute_path": os.path.abspath(path),
        "server_hostname": socket.gethostname()
    }
    
    # If path exists, try to list contents
    if os.path.exists(path) and os.path.isdir(path):
        try:
            contents = os.listdir(path)
            result["contents_count"] = len(contents)
            result["first_10_items"] = contents[:10]
        except Exception as e:
            result["list_error"] = str(e)
    
    # Check parent directory
    parent = os.path.dirname(path)
    result["parent_directory"] = parent
    result["parent_exists"] = os.path.exists(parent)
    
    if os.path.exists(parent) and os.path.isdir(parent):
        try:
            parent_contents = os.listdir(parent)
            result["parent_contents_count"] = len(parent_contents)
            result["parent_first_20_items"] = parent_contents[:20]
        except Exception as e:
            result["parent_list_error"] = str(e)
    
    logger.info(f"Path test result: {result}")
    return result

@app.get("/api/datasets")
def get_datasets(prefix: str = "plt"):
    global DATA_DIR
    if not os.path.exists(DATA_DIR):
        return {"datasets": []}
    
    datasets = [d for d in os.listdir(DATA_DIR) if d.startswith(prefix) and os.path.isdir(os.path.join(DATA_DIR, d))]
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
def _generate_plot_image(
    dataset_path: str,
    kind: str,
    axis: str,
    field: str,
    weight_field: Optional[str],
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
    width_value: Optional[float],
    width_unit: Optional[str],
    particles: tuple, # tuple to be hashable
    grids: bool,
    cell_edges: bool,
    timestamp: bool,
    top_left_text: Optional[str],
    top_right_text: Optional[str],
    short_size: float,
    font_size: int,
    scale_bar_height_fraction: float,
    colormap_fraction: float
):
    # Ensure global ds matches dataset_path
    global ds
    if ds is None or current_dataset_path != dataset_path:
        if os.path.exists(dataset_path):
            ds = yt.load(dataset_path)
            _add_derived_fields(ds)
        else:
            raise Exception(f"Dataset not found or mismatch: {dataset_path}")

    # Add derived fields if they are not already present (in case ds was loaded but fields not added)
    # This check is cheap
    if ("gas", "temperature") not in ds.derived_field_list and ("boxlib", "temperature") not in ds.derived_field_list:
         _add_derived_fields(ds)

    field_tuple = ("boxlib", field)
    # Check if field is a derived field we added
    if field in ["temperature", "velocity_magnitude", "momentum_density", "number_density"]:
        field_tuple = ("gas", field)
    
    # Fallback: if ("boxlib", field) is not found, check if ("gas", field) exists
    # This handles cases where we aliased gasDensity to ("gas", "density") but user requested "density"
    # which defaults to ("boxlib", "density")
    if field_tuple not in ds.derived_field_list and field_tuple not in ds.field_list:
        if ("gas", field) in ds.derived_field_list:
            field_tuple = ("gas", field)
        elif ("boxlib", field) not in ds.field_list:
             # Try to find a match in field_list
             # This is a bit hacky but might save us
             pass

    # Handle weight field for projections
    weight = None
    if kind == "prj" and weight_field and weight_field != "None":
        if weight_field == "density":
            weight = ("gas", "density")
        elif weight_field == "cell_volume":
            weight = ("boxlib", "volume") # or ("index", "cell_volume") depending on yt version/frontend
        elif weight_field == "cell_mass":
            weight = ("gas", "cell_mass")
        else:
            weight = ("boxlib", weight_field)

    if kind == "slc":
        slc = yt.SlicePlot(ds, axis, field_tuple, center=ds.domain_center)
    elif kind == "prj":
        slc = yt.ProjectionPlot(ds, axis, field_tuple, weight_field=weight, center=ds.domain_center)
    else:
        raise ValueError(f"Unknown plot kind: {kind}")
    
    # Set Width
    if width_value is not None and width_unit is not None:
        slc.set_width((width_value, width_unit))

    # Annotations
    if grids:
        slc.annotate_grids(edgecolors='white', linewidth=1)
    if cell_edges:
        slc.annotate_cell_edges(line_width=0.001, color='black')
    if not timestamp: # The argument is 'timestamp' (show it), but quick_plot logic was 'timeoff' (hide it). 
        # Wait, quick_plot says: if not time_off: slc.annotate_timestamp()
        # So if we want to show it, we call it.
        # But yt SlicePlot shows timestamp by default? 
        # Actually yt plots usually show timestamp by default. 
        # Let's assume 'timestamp' param means "show timestamp".
        # If it's False, we might need to hide it? 
        # yt.SlicePlot doesn't have a simple "hide timestamp" method other than not calling annotate_timestamp if it wasn't there, 
        # but it is there by default in some versions. 
        # Let's stick to: if timestamp is True, ensure it's there. 
        # Actually, let's look at quick_plot: "if not time_off: slc.annotate_timestamp()". 
        # This implies it might NOT be there by default or they want to ensure it.
        # Let's just call annotate_timestamp() if timestamp is True.
        pass
    else:
        # If user wants to hide it, we might need to do something else, but for now let's just add it if requested.
        # Actually, let's follow the requirement: "Toggle Timestamp".
        # If True, we add it.
        pass
    
    if timestamp:
        slc.annotate_timestamp()

    if particles:
        # particles is a tuple of strings
        for p_type in particles:
            if p_type in ds.particle_types:
                 slc.annotate_particles(0.1 * ds.domain_width[0], ptype=p_type, p_size=10, col='red') # Simplified for now
            else:
                print(f"Warning: Particle type {p_type} not found")

    if top_left_text:
        slc.annotate_text((0.02, 0.98), top_left_text, coord_system='axis', text_args={
                          'color': 'white', 'verticalalignment': 'top', 'horizontalalignment': 'left'})
    
    if top_right_text:
        slc.annotate_text((0.98, 0.98), top_right_text, coord_system='axis', text_args={
                          'color': 'white', 'verticalalignment': 'top', 'horizontalalignment': 'right'})

    
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
    image_data = np.array(frb[field_tuple])
    
    buf = io.BytesIO()
    
    # Common scale bar logic
    def add_scale_bar(ax, nx_pixels, ny_pixels):
        # Get axis information
        axis_id = ds.coordinates.axis_id[axis]
        x_ax_id = ds.coordinates.x_axis[axis_id]
        
        # Determine current width (might have been set by set_width)
        # slc.width is (width_x, width_y) in code units
        current_width = slc.width[0] # width in x
        
        # Use custom scale bar size if provided, otherwise auto-calculate
        if scale_bar_size is not None and scale_bar_unit is not None:
            try:
                custom_quantity = yt.YTQuantity(scale_bar_size, scale_bar_unit)
                box_length_fraction = float(custom_quantity / current_width)
                display_label = f'{scale_bar_size:.3g} {scale_bar_unit}'
            except Exception as e:
                print(f"Warning: Could not convert {scale_bar_size} {scale_bar_unit}: {e}")
                box_length_fraction = 0.2
                display_label = f'{0.2 * float(current_width.v):.3g} {current_width.units}'
        else:
            box_length_fraction = 0.2
            scale_value = 0.2 * float(current_width.v)
            magnitude = 10 ** np.floor(np.log10(scale_value))
            nice_scale = np.round(scale_value / magnitude) * magnitude
            box_length_fraction = nice_scale / float(current_width.v)
            display_label = f'{nice_scale:.3g} {current_width.units}'
        
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
                label = ds.field_info[field_tuple].get_label()
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

def _add_derived_fields(ds):
    # Constants
    m_u = 1.660539e-24 * unyt.g
    kelvin = unyt.K
    k_B = unyt.physical_constants.boltzmann_constant
    gamma = 5.0 / 3.0
    mean_molecular_weight = 1.0 # Default to 1.0 for now, could be parameterized
    mean_molecular_weight_per_H_atom = mean_molecular_weight * m_u

    # Alias gasDensity to ("gas", "density") if needed
    if ("gas", "density") not in ds.derived_field_list:
        if ("boxlib", "gasDensity") in ds.field_list:
            ds.add_field(("gas", "density"), function=lambda field, data: data[("boxlib", "gasDensity")] * unyt.g / unyt.cm**3, units="g/cm**3", sampling_type="cell", force_override=True)
    
    # Alias velocity components if needed (x-GasMomentum / gasDensity)
    # This is getting complicated. If the dataset has 'x-GasMomentum', it's likely momentum density.
    # Velocity = Momentum / Density
    if ("gas", "velocity_x") not in ds.derived_field_list:
        if ("boxlib", "x-GasMomentum") in ds.field_list and ("gas", "density") in ds.derived_field_list:
             ds.add_field(("gas", "velocity_x"), function=lambda field, data: (data[("boxlib", "x-GasMomentum")] * unyt.g / (unyt.cm**2 * unyt.s)) / data[("gas", "density")], units="cm/s", sampling_type="cell", force_override=True)
    if ("gas", "velocity_y") not in ds.derived_field_list:
        if ("boxlib", "y-GasMomentum") in ds.field_list and ("gas", "density") in ds.derived_field_list:
             ds.add_field(("gas", "velocity_y"), function=lambda field, data: (data[("boxlib", "y-GasMomentum")] * unyt.g / (unyt.cm**2 * unyt.s)) / data[("gas", "density")], units="cm/s", sampling_type="cell", force_override=True)
    if ("gas", "velocity_z") not in ds.derived_field_list:
        if ("boxlib", "z-GasMomentum") in ds.field_list and ("gas", "density") in ds.derived_field_list:
             ds.add_field(("gas", "velocity_z"), function=lambda field, data: (data[("boxlib", "z-GasMomentum")] * unyt.g / (unyt.cm**2 * unyt.s)) / data[("gas", "density")], units="cm/s", sampling_type="cell", force_override=True)

    # Total Energy Density
    if ("gas", "total_energy_density") not in ds.derived_field_list:
        if ("boxlib", "gasEnergy") in ds.field_list:
             # gasEnergy might be energy density or specific energy.
             # If it's energy density, it should have units of pressure (erg/cm^3).
             # If it's dimensionless in the file, we might need to multiply by a unit or assume code units.
             # Let's try to infer from the dataset.
             # For now, let's assume it's in code units which map to erg/cm^3 if properly scaled.
             # But yt complains it's dimensionless.
             # We can force units.
             ds.add_field(("gas", "total_energy_density"), function=lambda field, data: data[("boxlib", "gasEnergy")] * unyt.erg / unyt.cm**3, units="erg/cm**3", sampling_type="cell", force_override=True)


    # Number Density
    if ("gas", "number_density") not in ds.derived_field_list:
        def _number_density(field, data):
             return data[("gas", "density")] / mean_molecular_weight_per_H_atom
        ds.add_field(("gas", "number_density"), function=_number_density, units="cm**-3", sampling_type="cell", force_override=True)

    # Temperature
    if ("gas", "temperature") not in ds.derived_field_list:
        if ("boxlib", "temperature") in ds.field_list:
             def _temperature_boxlib(field, data):
                 return data[("boxlib", "temperature")] * kelvin
             ds.add_field(("gas", "temperature"), function=_temperature_boxlib, units="K", sampling_type="cell", force_override=True)
        else:
            def _temperature_derived(field, data):
                etot = data[("gas", "total_energy_density")]
                density = data[("gas", "density")]
                kinetic_energy = 0.5 * density * (
                    data[("gas", "velocity_x")]**2 + 
                    data[("gas", "velocity_y")]**2 + 
                    data[("gas", "velocity_z")]**2
                )
                eint = etot - kinetic_energy
                return eint * (gamma - 1.0) / (density / mean_molecular_weight_per_H_atom * k_B)
            ds.add_field(("gas", "temperature"), function=_temperature_derived, units="K", sampling_type="cell", force_override=True)

    # Velocity Magnitude
    if ("gas", "velocity_magnitude") not in ds.derived_field_list:
        def _velocity_magnitude(field, data):
            return np.sqrt(
                data[("gas", "velocity_x")]**2 + 
                data[("gas", "velocity_y")]**2 + 
                data[("gas", "velocity_z")]**2
            )
        ds.add_field(("gas", "velocity_magnitude"), function=_velocity_magnitude, units="cm/s", sampling_type="cell", force_override=True)

    # Momentum Density
    if ("gas", "momentum_density") not in ds.derived_field_list:
        def _momentum_density(field, data):
            return np.sqrt(
                data[("gas", "momentum_density_x")]**2 + 
                data[("gas", "momentum_density_y")]**2 + 
                data[("gas", "momentum_density_z")]**2
            )
        # Check if we have components
        if ("gas", "momentum_density_x") in ds.derived_field_list:
             ds.add_field(("gas", "momentum_density"), function=_momentum_density, sampling_type="cell", force_override=True)
        elif ("boxlib", "x-GasMomentum") in ds.field_list:
             # Alias components first if needed? 
             # Or just use them directly
             def _momentum_density_direct(field, data):
                 return np.sqrt(
                     (data[("boxlib", "x-GasMomentum")] * unyt.g / (unyt.cm**2 * unyt.s))**2 + 
                     (data[("boxlib", "y-GasMomentum")] * unyt.g / (unyt.cm**2 * unyt.s))**2 + 
                     (data[("boxlib", "z-GasMomentum")] * unyt.g / (unyt.cm**2 * unyt.s))**2
                 )
             ds.add_field(("gas", "momentum_density"), function=_momentum_density_direct, sampling_type="cell", force_override=True)


@app.get("/api/slice")
def get_slice(
    axis: str = "z", 
    field: str = "density", 
    kind: str = "slc",
    weight_field: Optional[str] = None,
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
    scale_bar_unit: Optional[str] = None,
    width_value: Optional[float] = None,
    width_unit: Optional[str] = None,
    particles: Optional[str] = None, # Comma separated string
    grids: bool = False,
    cell_edges: bool = False,
    timestamp: bool = False,
    top_left_text: Optional[str] = None,
    top_right_text: Optional[str] = None
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

    # Parse particles
    particle_list = tuple(p.strip() for p in particles.split(',')) if particles else ()

    try:
        if coord is None:
            coord = ds.domain_center[ds.coordinates.axis_id[axis]]
            coord = float(coord)
        
        image_bytes = _generate_plot_image(
            current_dataset_path,
            kind,
            axis,
            field,
            weight_field,
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
            width_value,
            width_unit,
            particle_list,
            grids,
            cell_edges,
            timestamp,
            top_left_text,
            top_right_text,
            SHORT_SIZE,
            FONT_SIZE,
            SCALE_BAR_HEIGHT_FRACTION,
            COLORMAP_FRACTION
        )
        
        return Response(content=image_bytes, media_type="image/png")

    except Exception as e:
        print(f"Error generating plot: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fields")
def get_fields():
    global ds
    if ds is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
    
    # Ensure derived fields are added
    _add_derived_fields(ds)
    
    # Return a list of fluid fields
    # We want boxlib fields + our derived fields
    fields = [f[1] for f in ds.field_list if f[0] == 'boxlib']
    
    # Add our derived fields if they exist
    derived_fields = ["temperature", "velocity_magnitude", "momentum_density", "number_density"]
    for df in derived_fields:
        if ("gas", df) in ds.derived_field_list:
            fields.append(df)
            
    # Sort and unique
    fields = sorted(list(set(fields)))
    return {"fields": fields}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9010)
