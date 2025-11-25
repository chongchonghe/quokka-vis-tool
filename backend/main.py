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
    level=logging.FATAL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backend_debug.log')
    ]
)
logger = logging.getLogger(__name__)

yt.set_log_level(40) # 40 = Error

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# Initial load to set defaults if needed, or just rely on load_config in endpoints
# We can keep defaults as fallback
DEFAULT_CONFIG = {
    "short_size": 3.6,
    "font_size": 20,
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
    
    # Add derived fields if not already present
    if ("gas", "temperature") not in ds.derived_field_list:
        _add_derived_fields(ds)
    
    # Return a list of gas fields (with the custom yt fork, all fields are in the "gas" namespace)
    # ds.field_list is a list of tuples (field_type, field_name)
    # We want the field_name for gas fields
    fields = [f[1] for f in ds.field_list if f[0] == 'gas']
    
    # Also include derived fields
    derived_fields = [f[1] for f in ds.derived_field_list if f[0] == 'gas']
    
    # Combine and remove duplicates
    all_fields = list(set(fields + derived_fields))
    all_fields.sort()
    
    return {"fields": all_fields}


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
    timestamp: bool,
    top_left_text: Optional[str],
    top_right_text: Optional[str],
    short_size: float,
    font_size: int,
    scale_bar_height_fraction: float,
    colormap_fraction: float,
    show_axes: bool
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
    if ("gas", "temperature") not in ds.derived_field_list:
         _add_derived_fields(ds)

    # With the custom yt fork, all fields are defined as ("gas", field_name)
    field_tuple = ("gas", field)
    
    # Handle weight field for projections
    weight = None
    if kind == "prj" and weight_field and weight_field != "None":
        if weight_field == "density":
            weight = ("gas", "density")
        elif weight_field == "cell_volume":
            weight = ("index", "cell_volume")  # Standard yt field for cell volume
        elif weight_field == "cell_mass":
            weight = ("gas", "cell_mass")
        else:
            weight = ("gas", weight_field)

    # Create plot object
    if kind == "slc":
        slc = yt.SlicePlot(ds, axis, field_tuple, center=ds.domain_center)
    elif kind == "prj":
        slc = yt.ProjectionPlot(ds, axis, field_tuple, weight_field=weight, center=ds.domain_center)
    else:
        raise ValueError(f"Unknown plot kind: {kind}")
    
    # ========================================
    # Configure plot properties
    # ========================================
    slc.set_cmap(field_tuple, cmap)
    slc.set_log(field_tuple, log_scale)
    slc.set_background_color(field_tuple, 'black')
    
    # Set width if provided
    if width_value is not None and width_unit is not None:
        slc.set_width((width_value, width_unit))
    
    # Set colorbar label (do this before setting zlim)
    if show_colorbar:
        if colorbar_label:
            label = colorbar_label
        else:
            try:
                # For projection plots without weight field, yt integrates along the axis
                # so the units become field_unit * length_unit
                if kind == "prj" and weight is None:
                    # Get the field info
                    field_info = ds.field_info[field_tuple]
                    # Get the base field label (without units)
                    field_name = field_info.display_name
                    # Get the field units
                    field_units = field_info.units
                    # Get the length unit from the dataset
                    length_unit = ds.length_unit
                    # Construct the integrated units
                    integrated_units = field_units * length_unit
                    # Create the label with integrated units
                    label = f"{field_name} ({integrated_units})"
                else:
                    # For slice plots or weighted projections, use the standard label
                    label = ds.field_info[field_tuple].get_label()
            except Exception as e:
                print(f"Warning: Could not get field label: {e}")
                label = field
        
        slc.set_colorbar_label(field_tuple, label)
    
    # Set vmin/vmax if provided
    if vmin is not None and vmax is not None:
        slc.set_zlim(field_tuple, vmin, vmax)
    elif vmin is not None:
        slc.set_zlim(field_tuple, vmin, 'max')
    elif vmax is not None:
        slc.set_zlim(field_tuple, 'min', vmax)
    
    # ========================================
    # Add annotations
    # ========================================
    if particles:
        # Check if particles exist in the dataset
        # Following quick_plot logic: check particle_info and verify particles exist
        if 'particles' in ds.parameters.keys():
            ad = ds.all_data()
            Lx = ds.domain_right_edge[0] - ds.domain_left_edge[0]
            for p_type in particles:
                # Check if particle type exists in particle_info
                if p_type not in ds['particle_info'].keys():
                    print(f"Warning: Particle type {p_type} not found in particle_info")
                    continue
                
                num_particles = ds['particle_info'][p_type]['num_particles']
                if num_particles == 0:
                    print(f"Warning: No {p_type} particles in dataset")
                    continue
                
                # Verify particle position field exists
                try:
                    pos = ad[(p_type, "particle_position_x")]
                    if len(pos) > 0:
                        # Annotate particles at a depth of 0.1 * boxsize
                        slc.annotate_particles(Lx * 0.1, p_size=10, col='red', marker='o', ptype=p_type)
                    else:
                        print(f"Warning: No {p_type} particles found in all_data()")
                except yt.utilities.exceptions.YTFieldNotFound:
                    print(f"Warning: Particle position field not found for {p_type}")
                    continue
        else:
            print("Warning: No particles in ds.parameters")
    
    if grids:
        slc.annotate_grids(edgecolors='white', linewidth=1)
    
    if timestamp:
        slc.annotate_timestamp(corner='upper_left')
    
    # ========================================
    # Configure figure properties
    # ========================================
    # Calculate figure size based on aspect ratio and SHORT_SIZE
    axis_id = ds.coordinates.axis_id[axis]
    x_ax_id = ds.coordinates.x_axis[axis_id]
    y_ax_id = ds.coordinates.y_axis[axis_id]
    
    Wx = ds.domain_width[x_ax_id].v
    Wy = ds.domain_width[y_ax_id].v
    aspect = float(Wy / Wx)
    
    scale_bar_x_loc = 0.5 if aspect > 1.3 else 0.15
    scale_bar_y_loc = 0.15 if aspect < 1/1.3 else 0.1
    scale_bar_pos = (scale_bar_x_loc, scale_bar_y_loc)
    if scale_bar_size is not None and scale_bar_unit is not None:
        # Use custom scale bar size - positioned at lower center using pos parameter
        slc.annotate_scale(coeff=scale_bar_size, unit=scale_bar_unit, 
                          pos=scale_bar_pos, coord_system='axis',
                          min_frac=0.05, max_frac=0.16,
                          size_bar_args={'pad': 0.55, 'sep': 8, 'borderpad': 5, 'color': 'w'})
    elif show_scale_bar:
        # Use automatic scale bar (20% of width) - positioned at lower center
        slc.annotate_scale(pos=scale_bar_pos, coord_system='axis',
                          min_frac=0.05, max_frac=0.16,
                          size_bar_args={'pad': 0.55, 'sep': 8, 'borderpad': 5, 'color': 'w'})
    
    if top_left_text:
        slc.annotate_text((0.02, 0.98), top_left_text, coord_system='axis', text_args={
                          'color': 'white', 'verticalalignment': 'top', 'horizontalalignment': 'left'})
    
    if top_right_text:
        slc.annotate_text((0.98, 0.98), top_right_text, coord_system='axis', text_args={
                          'color': 'white', 'verticalalignment': 'top', 'horizontalalignment': 'right'})
    
    is_close_to_square = aspect < 4.1 / 3 and aspect > 3.0 / 4.1
    if aspect > 1:
        # Height > Width. Width is short side.
        fig_width = short_size
        fig_height = short_size * aspect
        # set_figure_size sets the long dimension
        fig_size = fig_height * 1.5 if is_close_to_square else fig_height
        slc.set_figure_size(fig_size)
    else:
        # Width >= Height. Height is short side.
        fig_height = short_size
        fig_width = short_size / aspect
        # set_figure_size sets the long dimension
        fig_size = fig_width * 1.5 if is_close_to_square else fig_width
        slc.set_figure_size(fig_size)
    slc.set_font_size(font_size)
    
    # ========================================
    # Handle visibility controls
    # ========================================
    if not show_axes:
        slc.hide_axes(draw_frame=True)
    
    if not show_colorbar:
        slc.set_colorbar_label(field_tuple, "")
        slc.hide_colorbar()
    
    # Save to temporary file then read into BytesIO
    # yt.save() requires a file path, not a BytesIO object
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        slc.save(tmp_path, mpl_kwargs={"dpi": dpi, "bbox_inches": "tight", "pad_inches": 0.05})
        # Read the saved file into bytes
        with open(tmp_path, 'rb') as f:
            image_bytes = f.read()
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    return image_bytes

def _add_derived_fields(ds):
    """
    Add derived fields to the dataset.
    With the custom yt fork, standard fields like density, velocity_x, etc. are already
    defined as ("gas", "density"), ("gas", "velocity_x"), etc.
    We only need to add the custom derived fields like temperature, velocity_magnitude, etc.
    """
    # Constants
    m_u = 1.660539e-24 * unyt.g
    kelvin = unyt.K
    k_B = unyt.physical_constants.boltzmann_constant
    gamma = 5.0 / 3.0
    mean_molecular_weight = 1.0  # Default to 1.0 for now, could be parameterized
    mean_molecular_weight_per_H_atom = mean_molecular_weight * m_u

    # Number Density
    if ("gas", "number_density") not in ds.derived_field_list:
        def _number_density(field, data):
            return data[("gas", "density")] / mean_molecular_weight_per_H_atom
        ds.add_field(("gas", "number_density"), function=_number_density, units="cm**-3", sampling_type="cell", force_override=True)

    # Temperature (if not already present)
    if ("gas", "temperature") not in ds.derived_field_list:
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
        ds.add_field(("gas", "momentum_density"), function=_momentum_density, sampling_type="cell", force_override=True)


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
    FONT_SIZE = config.get("font_size", 20)
    SCALE_BAR_HEIGHT_FRACTION = config.get("scale_bar_height_fraction", 15)
    COLORMAP_FRACTION = config.get("colormap_fraction", 0.1)
    SHOW_AXES = config.get("show_axes", False)

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
            timestamp,
            top_left_text,
            top_right_text,
            SHORT_SIZE,
            FONT_SIZE,
            SCALE_BAR_HEIGHT_FRACTION,
            COLORMAP_FRACTION,
            SHOW_AXES
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
