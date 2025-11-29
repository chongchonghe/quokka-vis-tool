from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response
import yt
from yt.utilities.exceptions import YTCannotParseUnitDisplayName
import unyt
import os
from typing import List, Optional
from functools import lru_cache
import io
import matplotlib
matplotlib.use('Agg')
# Optimize matplotlib performance
matplotlib.rcParams['text.usetex'] = False
matplotlib.rcParams['path.simplify'] = True
matplotlib.rcParams['path.simplify_threshold'] = 1.0
matplotlib.rcParams['agg.path.chunksize'] = 10000
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
import subprocess
import tempfile
import zipfile
from datetime import datetime
import shutil

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
    particle_size: int,
    particle_color: str,
    grids: bool,
    timestamp: bool,
    top_left_text: Optional[str],
    top_right_text: Optional[str],
    short_size: float,
    font_size: int,
    scale_bar_height_fraction: float,
    colormap_fraction: float,
    show_axes: bool,
    field_unit: Optional[str],
    # 3D rendering params
    camera_x: float,
    camera_y: float,
    camera_z: float,
    n_layers: int,
    alpha_min: float,
    alpha_max: float,
    preview: bool
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
    elif kind == "vol":
        # Volume rendering
        # We handle this separately because it returns a scene, not a plot container like SlicePlot
        pass
    else:
        raise ValueError(f"Unknown plot kind: {kind}")
    
    # ========================================
    # Volume Rendering Handling
    # ========================================
    if kind == "vol":
        print(f"Creating volume rendering for {field}...")
        sc = yt.create_scene(ds, field=field_tuple)
        source = sc[0]
        
        # Set up transfer function
        bounds = ds.all_data().quantities.extrema(field_tuple)
        
        if log_scale:
            real_bounds = np.log10(bounds)
            # Heuristic: if range is too large or small, adjust? 
            # For now, just ensure min is not too small relative to max if it's density
            # visualize_3d.py uses: real_bounds[0] = real_bounds[1] - 8
            if real_bounds[1] - real_bounds[0] > 8:
                real_bounds[0] = real_bounds[1] - 8
        else:
            real_bounds = bounds
            
        tf = yt.ColorTransferFunction(real_bounds)
        tf.add_layers(n_layers, w=0.02, colormap=cmap, alpha=np.logspace(np.log10(alpha_min), np.log10(alpha_max), n_layers))
        
        source.tfh.tf = tf
        source.tfh.bounds = bounds
        source.tfh.set_log(log_scale)
        
        # Camera setup
        cam = sc.camera
        # Resolution: use a fixed reasonable size or base on short_size * dpi?
        # visualize_3d uses (1024, 1024) as standard.
        # Let's use dpi * short_size roughly
        if preview:
            res_px = 512
        else:
            res_px = int(short_size * dpi)
        cam.resolution = (res_px, res_px)
        
        # Camera direction
        view_dir = np.array([camera_x, camera_y, camera_z], dtype=float)
        norm = np.linalg.norm(view_dir)
        if norm == 0:
            view_dir = np.array([1.0, 1.0, 1.0])
        else:
            view_dir = view_dir / norm
            
        # North vector
        if abs(view_dir[2]) > 0.9:
            north = np.array([0, 1, 0])
        else:
            north = np.array([0, 0, 1])
            
        # Width
        # Default width is 1.0 * domain_width if not specified
        width_factor = 1.0
        if width_value is not None and width_unit is not None:
             # Convert width to code units relative to domain width?
             # yt camera set_width takes (value, unit)
             cam.set_width((width_value, width_unit))
        else:
             # Smart width logic:
             # 1. Find the longest side
             domain_width = ds.domain_width
             max_dim_idx = np.argmax(domain_width)
             max_width = domain_width[max_dim_idx]
             
             # 2. Check if looking along the longest side (small angle)
             # view_dir is normalized. Check component along max_dim_idx.
             # If abs(view_dir[max_dim_idx]) is close to 1, we are looking along that axis.
             if abs(view_dir[max_dim_idx]) > 0.9:
                 # Looking along the longest side. Use the shortest side.
                 min_width = np.min(domain_width)
                 cam.set_width(min_width)
             else:
                 # Not looking along the longest side. Use the longest side.
                 cam.set_width(max_width)
             
        # Position
        # We need to calculate position based on width and focus
        # visualize_3d.py: cam_pos = ds.domain_center + 1.5 * width * ds.domain_width * view_dir
        # But cam.set_width sets the view width. The distance depends on the width.
        # If we use switch_orientation, it handles looking at focus.
        
        cam.set_focus(ds.domain_center)
        cam.switch_orientation(normal_vector=view_dir, north_vector=north)
        
        # Adjust position distance to fit the width?
        # switch_orientation keeps the current distance or sets a default?
        # Actually, let's just trust switch_orientation and set_width.
        # But visualize_3d.py explicitly sets position.
        # Let's try to match visualize_3d.py logic for position if possible, 
        # but set_width should handle the field of view.
        
        # Render
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            sc.save(tmp_path, sigma_clip=4.0)
            with open(tmp_path, 'rb') as f:
                image_bytes = f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
        return image_bytes

    # ========================================
    # Configure plot properties (Slice/Projection)
    # ========================================
    # Set units if specified (for custom unit display)
    if field_unit is not None and field_unit != "":
        try:
            slc.set_unit(field_tuple, field_unit)
        except Exception as e:
            print(f"Warning: Could not set unit '{field_unit}' for field {field_tuple}: {e}")
    
    slc.set_cmap(field_tuple, cmap)
    slc.set_log(field_tuple, log_scale)
    slc.set_background_color(field_tuple, 'black')
    
    # Set width if provided
    is_squared = False
    if width_value is not None and width_unit is not None:
        slc.set_width((width_value, width_unit))
        is_squared = True
    
    # Set colorbar label only if user provides a custom one
    # YT automatically generates proper labels with units otherwise
    if show_colorbar and colorbar_label:
        slc.set_colorbar_label(field_tuple, colorbar_label)
    
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
                        slc.annotate_particles(Lx * 0.1, p_size=particle_size, col=particle_color, marker='o', ptype=p_type)
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
    real_aspect = aspect if not is_squared else 1.0
    
    scale_bar_x_loc = 0.5 if real_aspect > 1.3 else 0.15
    scale_bar_y_loc = 0.15 if real_aspect < 1/1.3 else 0.1
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
    is_make_bigger = is_close_to_square # always make it bigger for close-to-square plots
    if not is_squared:
        if aspect > 1:
            # Height > Width. Width is short side.
            fig_width = short_size
            fig_height = short_size * aspect
            # set_figure_size sets the long dimension
            fig_size = fig_height * 1.5 if is_make_bigger else fig_height
            slc.set_figure_size(fig_size)
        else:
            # Width >= Height. Height is short side.
            fig_height = short_size
            fig_width = short_size / aspect
            # set_figure_size sets the long dimension
            fig_size = fig_width * 1.5 if is_make_bigger else fig_width
            slc.set_figure_size(fig_size)
    else:
        # square plot, make it bigger
        fig_size = short_size * 1.5
        slc.set_figure_size(fig_size)
        
    slc.set_font_size(font_size)
    
    # ========================================
    # Handle visibility controls
    # ========================================
    if not show_axes:
        slc.hide_axes(draw_frame=True)
    
    if not show_colorbar:
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
    except YTCannotParseUnitDisplayName as e:
        # LaTeX parsing error in colorbar label - retry with simple field name
        print(f"Warning: LaTeX parsing error in colorbar label: {e}")
        print(f"Retrying with simplified colorbar label: {field}")
        slc.set_colorbar_label(field_tuple, field)
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
        try:
            # Let YT automatically determine units from the calculation
            ds.add_field(("gas", "number_density"), function=_number_density, 
                        units="auto", sampling_type="cell", force_override=True,
                        display_name="Number Density")
        except Exception as e:
            print(f"Warning: Could not add number density field: {e}")
            pass

    # Temperature (if not already present)
    if ("gas", "temperature") not in ds.derived_field_list:
        # Check if total_energy_density field exists
        has_total_energy = (
            ("gas", "total_energy_density") in ds.field_list or 
            ("gas", "total_energy_density") in ds.derived_field_list
        )
        
        if has_total_energy:
            # Use total_energy_density to derive temperature
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
            try:
                # Let YT automatically determine units from the calculation
                ds.add_field(("gas", "temperature"), function=_temperature_derived, 
                           units="auto", sampling_type="cell", force_override=True,
                           display_name="Temperature")
                print("Temperature field added using total_energy_density")
            except Exception as e:
                print(f"Warning: Could not add temperature field via total_energy_density: {e}")
        else:
            # Fall back to internal_energy_density
            has_internal_energy = (
                ("gas", "internal_energy_density") in ds.field_list or 
                ("gas", "internal_energy_density") in ds.derived_field_list
            )
            
            if has_internal_energy:
                def _temperature_from_internal(field, data):
                    return data[("gas", "internal_energy_density")] * (gamma - 1.0) / (data[("gas", "density")] / mean_molecular_weight_per_H_atom * k_B)
                try:
                    # Let YT automatically determine units from the calculation
                    ds.add_field(("gas", "temperature"), function=_temperature_from_internal, 
                               units="auto", sampling_type="cell", force_override=True,
                               display_name="Temperature")
                    print("Temperature field added using internal_energy_density")
                except Exception as e:
                    print(f"Warning: Could not add temperature field via internal_energy_density: {e}")
            else:
                print("Warning: Neither total_energy_density nor internal_energy_density found. Temperature field not added.")

    # Velocity Magnitude
    if ("gas", "velocity_magnitude") not in ds.derived_field_list:
        def _velocity_magnitude(field, data):
            return np.sqrt(
                data[("gas", "velocity_x")]**2 + 
                data[("gas", "velocity_y")]**2 + 
                data[("gas", "velocity_z")]**2
            )
        try:
            # Let YT automatically determine units from the calculation
            ds.add_field(("gas", "velocity_magnitude"), function=_velocity_magnitude, 
                        units="auto", sampling_type="cell", force_override=True,
                        display_name="Velocity Magnitude")
        except Exception as e:
            print(f"Warning: Could not add velocity magnitude field: {e}")
            pass

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
    particle_size: Optional[int] = None,
    particle_color: str = "red",
    grids: bool = False,
    timestamp: bool = False,
    top_left_text: Optional[str] = None,
        top_right_text: Optional[str] = None,
        field_unit: Optional[str] = None,
        # 3D params
        camera_x: float = 1.0,
        camera_y: float = 1.0,
        camera_z: float = 1.0,
        n_layers: int = 5,
        alpha_min: float = 0.1,
        alpha_max: float = 1.0,
        preview: bool = False
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
    DEFAULT_PARTICLE_SIZE = config.get("default_particle_size", 10)

    # Parse particles
    particle_list = tuple(p.strip() for p in particles.split(',')) if particles else ()
    
    # Use provided particle_size or default
    p_size = particle_size if particle_size is not None else DEFAULT_PARTICLE_SIZE

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
            p_size,
            particle_color,
            grids,
            timestamp,
            top_left_text,
            top_right_text,
            SHORT_SIZE,
            FONT_SIZE,
            SCALE_BAR_HEIGHT_FRACTION,
            COLORMAP_FRACTION,
            SHOW_AXES,
            field_unit,
            camera_x,
            camera_y,
            camera_z,
            n_layers,
            alpha_min,
            alpha_max,
            preview
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
    derived_fields = ["temperature", "velocity_magnitude", "number_density"]
    for df in derived_fields:
        if ("gas", df) in ds.derived_field_list:
            fields.append(df)
            
    # Sort and unique
    fields = sorted(list(set(fields)))
    return {"fields": fields}

@app.get("/api/particle_types")
def get_particle_types():
    """
    Get the list of available particle types from config.yaml.
    Each type is returned with '_particles' appended (e.g., 'Rad' -> 'Rad_particles')
    Also returns the default particle size.
    """
    try:
        config = load_config()
        particle_types = config.get("particle_types", [])
        default_particle_size = config.get("default_particle_size", 10)
        # Append '_particles' to each type
        particle_types_with_suffix = [f"{ptype}_particles" for ptype in particle_types]
        return {
            "particle_types": particle_types_with_suffix,
            "default_particle_size": default_particle_size
        }
    except Exception as e:
        print(f"Error loading particle types: {e}")
        # Return default list if config can't be loaded (with '_particles' suffix)
        return {
            "particle_types": ["Rad_particles", "CIC_particles", "CICRad_particles", "StochasticStellarPop_particles", "Sink_particles"],
            "default_particle_size": 10
        }

@app.get("/api/export/current_frame")
def export_current_frame(
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
    particles: Optional[str] = None,
    particle_size: Optional[int] = None,
    particle_color: str = "red",
    grids: bool = False,
    timestamp: bool = False,
    top_left_text: Optional[str] = None,
    top_right_text: Optional[str] = None,
    field_unit: Optional[str] = None
):
    """Export the current frame as a downloadable PNG file"""
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
    DEFAULT_PARTICLE_SIZE = config.get("default_particle_size", 10)

    # Parse particles
    particle_list = tuple(p.strip() for p in particles.split(',')) if particles else ()
    
    # Use provided particle_size or default
    p_size = particle_size if particle_size is not None else DEFAULT_PARTICLE_SIZE

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
            p_size,
            particle_color,
            grids,
            timestamp,
            top_left_text,
            top_right_text,
            SHORT_SIZE,
            FONT_SIZE,
            SCALE_BAR_HEIGHT_FRACTION,
            COLORMAP_FRACTION,
            SHOW_AXES,
            field_unit
        )
        
        # Get current dataset name
        dataset_name = os.path.basename(current_dataset_path)
        filename = f"{dataset_name}_{field}_{axis}.png"
        
        return Response(
            content=image_bytes, 
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        print(f"Error generating plot: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/animation")
def export_animation(request: Request):
    """
    Export animation as PNG frames + GIF + MP4 bundled in a ZIP file.
    PNGs are always exported even if ffmpeg is not available or fails.
    Expects JSON body with:
    - datasets: list of dataset filenames
    - fps: frames per second for GIF/MP4
    - all visualization parameters (axis, field, etc.)
    """
    global DATA_DIR
    
    temp_dir = None
    
    try:
        # Parse request body
        import asyncio
        body = asyncio.run(request.json())
        
        # Validate and sanitize input parameters
        datasets = body.get("datasets", [])
        if not datasets or not isinstance(datasets, list):
            raise HTTPException(status_code=400, detail="No datasets provided or invalid format")
        
        fps = body.get("fps", 5)
        if not isinstance(fps, (int, float)) or fps <= 0:
            print(f"Warning: Invalid fps value {fps}, defaulting to 5")
            fps = 5
        
        # Visualization parameters
        axis = body.get("axis", "z")
        field = body.get("field", "density")
        kind = body.get("kind", "slc")
        weight_field = body.get("weight_field")
        vmin = body.get("vmin")
        vmax = body.get("vmax")
        show_colorbar = body.get("show_colorbar", False)
        log_scale = body.get("log_scale", True)
        colorbar_label = body.get("colorbar_label")
        colorbar_orientation = body.get("colorbar_orientation", "right")
        cmap = body.get("cmap", "viridis")
        dpi = body.get("dpi", 300)
        
        # Validate dpi
        if not isinstance(dpi, (int, float)) or dpi <= 0 or dpi > 1000:
            print(f"Warning: Invalid dpi value {dpi}, defaulting to 300")
            dpi = 300
        
        show_scale_bar = body.get("show_scale_bar", False)
        scale_bar_size = body.get("scale_bar_size")
        scale_bar_unit = body.get("scale_bar_unit")
        width_value = body.get("width_value")
        width_unit = body.get("width_unit")
        particles = body.get("particles", "")
        particle_size = body.get("particle_size")
        particle_color = body.get("particle_color", "red")
        grids = body.get("grids", False)
        timestamp_anno = body.get("timestamp", False)
        top_left_text = body.get("top_left_text")
        top_right_text = body.get("top_right_text")
        field_unit = body.get("field_unit")
        
        # Validate DATA_DIR
        if not DATA_DIR or not os.path.exists(DATA_DIR):
            raise HTTPException(status_code=400, detail=f"Data directory does not exist: {DATA_DIR}")
        
        # Load configuration
        try:
            config = load_config()
            SHORT_SIZE = config.get("short_size", 3.6)
            FONT_SIZE = config.get("font_size", 20)
            SCALE_BAR_HEIGHT_FRACTION = config.get("scale_bar_height_fraction", 15)
            COLORMAP_FRACTION = config.get("colormap_fraction", 0.1)
            SHOW_AXES = config.get("show_axes", False)
            DEFAULT_PARTICLE_SIZE = config.get("default_particle_size", 10)
        except Exception as e:
            print(f"Warning: Could not load config, using defaults: {e}")
            SHORT_SIZE = 3.6
            FONT_SIZE = 20
            SCALE_BAR_HEIGHT_FRACTION = 15
            COLORMAP_FRACTION = 0.1
            SHOW_AXES = False
            DEFAULT_PARTICLE_SIZE = 10
        
        # Use provided particle_size or default
        p_size = particle_size if particle_size is not None else DEFAULT_PARTICLE_SIZE
        
        # Parse particles
        particle_list = tuple(p.strip() for p in particles.split(',')) if particles else ()
        
        # Create temporary directory for all files
        try:
            temp_dir = tempfile.mkdtemp()
            print(f"Created temporary directory: {temp_dir}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create temporary directory: {e}")
        
        # Track successfully generated frames
        generated_frames = []
        failed_frames = []
        
        try:
            # Generate PNG frames
            print(f"Generating {len(datasets)} frames...")
            for idx, dataset_name in enumerate(datasets):
                try:
                    # Validate dataset name
                    if not dataset_name or not isinstance(dataset_name, str):
                        print(f"Warning: Invalid dataset name at index {idx}: {dataset_name}")
                        failed_frames.append((idx, dataset_name, "Invalid dataset name"))
                        continue
                    
                    dataset_path = os.path.join(DATA_DIR, dataset_name)
                    
                    if not os.path.exists(dataset_path):
                        print(f"Warning: Dataset not found: {dataset_path}")
                        failed_frames.append((idx, dataset_name, "Dataset not found"))
                        continue
                    
                    # Load dataset
                    ds_temp = yt.load(dataset_path)
                    _add_derived_fields(ds_temp)
                    
                    # Get coordinate
                    coord = ds_temp.domain_center[ds_temp.coordinates.axis_id[axis]]
                    coord = float(coord)
                    
                    # Generate image
                    image_bytes = _generate_plot_image(
                        dataset_path,
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
                        p_size,
                        particle_color,
                        grids,
                        timestamp_anno,
                        top_left_text,
                        top_right_text,
                        SHORT_SIZE,
                        FONT_SIZE,
                        SCALE_BAR_HEIGHT_FRACTION,
                        COLORMAP_FRACTION,
                        SHOW_AXES,
                        field_unit
                    )
                    
                    # Save PNG frame
                    frame_filename = f"frame_{idx:04d}_{dataset_name}_{field}_{axis}.png"
                    frame_path = os.path.join(temp_dir, frame_filename)
                    with open(frame_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    generated_frames.append(frame_filename)
                    print(f"Generated frame {idx + 1}/{len(datasets)}: {frame_filename}")
                    
                except Exception as e:
                    print(f"Error generating frame {idx} for dataset {dataset_name}: {e}")
                    traceback.print_exc()
                    failed_frames.append((idx, dataset_name, str(e)))
                    continue
            
            # Check if we have any frames
            if not generated_frames:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate any frames. Please check the server logs for details."
                )
            
            print(f"Successfully generated {len(generated_frames)} frames")
            if failed_frames:
                print(f"Failed to generate {len(failed_frames)} frames:")
                for idx, name, error in failed_frames:
                    print(f"  Frame {idx} ({name}): {error}")
            
            # Try to create GIF and MP4 using ffmpeg (optional, won't fail if ffmpeg unavailable)
            gif_path = None
            mp4_path = None
            ffmpeg_available = False
            
            # Check if ffmpeg is available
            try:
                result = subprocess.run(
                    ["ffmpeg", "-version"], 
                    capture_output=True, 
                    check=True,
                    timeout=5
                )
                ffmpeg_available = True
                print("ffmpeg is available")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                print(f"ffmpeg is not available or failed: {e}")
                print("Will export PNG frames only")
            
            if ffmpeg_available and len(generated_frames) > 1:
                # Create GIF using ffmpeg
                try:
                    print("Creating animated GIF...")
                    gif_filename = f"animation_{field}_{axis}.gif"
                    gif_path = os.path.join(temp_dir, gif_filename)
                    palette_path = os.path.join(temp_dir, "palette.png")
                    
                    # Generate palette for better quality GIF
                    palette_cmd = [
                        "ffmpeg", "-y",
                        "-framerate", str(fps),
                        "-pattern_type", "glob",
                        "-i", os.path.join(temp_dir, "frame_*.png"),
                        "-vf", "palettegen",
                        palette_path
                    ]
                    result = subprocess.run(palette_cmd, capture_output=True, check=True, timeout=60)
                    
                    # Create GIF with palette
                    gif_cmd = [
                        "ffmpeg", "-y",
                        "-framerate", str(fps),
                        "-pattern_type", "glob",
                        "-i", os.path.join(temp_dir, "frame_*.png"),
                        "-i", palette_path,
                        "-lavfi", "paletteuse",
                        gif_path
                    ]
                    result = subprocess.run(gif_cmd, capture_output=True, check=True, timeout=120)
                    
                    if os.path.exists(gif_path) and os.path.getsize(gif_path) > 0:
                        print(f"Created GIF: {gif_filename}")
                    else:
                        print("GIF creation failed: output file is empty or doesn't exist")
                        gif_path = None
                        
                except subprocess.TimeoutExpired:
                    print("GIF creation timed out")
                    gif_path = None
                except Exception as e:
                    print(f"Error creating GIF: {e}")
                    traceback.print_exc()
                    gif_path = None
                
                # Create MP4 using ffmpeg
                try:
                    print("Creating MP4 video...")
                    mp4_filename = f"animation_{field}_{axis}.mp4"
                    mp4_path = os.path.join(temp_dir, mp4_filename)
                    
                    mp4_cmd = [
                        "ffmpeg", "-y",
                        "-framerate", str(fps),
                        "-pattern_type", "glob",
                        "-i", os.path.join(temp_dir, "frame_*.png"),
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        mp4_path
                    ]
                    result = subprocess.run(mp4_cmd, capture_output=True, check=True, timeout=120)
                    
                    if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
                        print(f"Created MP4: {mp4_filename}")
                    else:
                        print("MP4 creation failed: output file is empty or doesn't exist")
                        mp4_path = None
                        
                except subprocess.TimeoutExpired:
                    print("MP4 creation timed out")
                    mp4_path = None
                except Exception as e:
                    print(f"Error creating MP4: {e}")
                    traceback.print_exc()
                    mp4_path = None
            elif not ffmpeg_available:
                print("Skipping GIF and MP4 creation: ffmpeg not available")
            elif len(generated_frames) <= 1:
                print("Skipping GIF and MP4 creation: need at least 2 frames")
            
            # Create ZIP file (always includes PNGs, optionally includes GIF/MP4)
            print("Creating ZIP archive...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"export_{field}_{axis}_{timestamp}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add all PNG frames
                    png_count = 0
                    for filename in sorted(os.listdir(temp_dir)):
                        if filename.startswith("frame_") and filename.endswith(".png"):
                            file_path = os.path.join(temp_dir, filename)
                            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                zipf.write(file_path, filename)
                                png_count += 1
                    
                    print(f"Added {png_count} PNG frames to ZIP")
                    
                    # Add GIF if it was created successfully
                    if gif_path and os.path.exists(gif_path) and os.path.getsize(gif_path) > 0:
                        zipf.write(gif_path, os.path.basename(gif_path))
                        print(f"Added GIF to ZIP")
                    
                    # Add MP4 if it was created successfully
                    if mp4_path and os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
                        zipf.write(mp4_path, os.path.basename(mp4_path))
                        print(f"Added MP4 to ZIP")
                    
                    # Add a README with information about the export
                    readme_content = f"""Animation Export Summary
========================

Export Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Field: {field}
Axis: {axis}
FPS: {fps}
DPI: {dpi}

Total Datasets Requested: {len(datasets)}
Successfully Generated Frames: {len(generated_frames)}
Failed Frames: {len(failed_frames)}

PNG Frames: {png_count}
GIF Created: {'Yes' if gif_path and os.path.exists(gif_path) else 'No'}
MP4 Created: {'Yes' if mp4_path and os.path.exists(mp4_path) else 'No'}
FFmpeg Available: {'Yes' if ffmpeg_available else 'No'}

"""
                    if failed_frames:
                        readme_content += "\nFailed Frames:\n"
                        for idx, name, error in failed_frames:
                            readme_content += f"  Frame {idx} ({name}): {error}\n"
                    
                    zipf.writestr("README.txt", readme_content)
                    
                print(f"Created ZIP: {zip_filename}")
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create ZIP file: {e}")
            
            # Read ZIP file into memory
            if not os.path.exists(zip_path):
                raise HTTPException(status_code=500, detail="ZIP file was not created successfully")
            
            with open(zip_path, 'rb') as f:
                zip_bytes = f.read()
            
            if not zip_bytes:
                raise HTTPException(status_code=500, detail="ZIP file is empty")
            
            return Response(
                content=zip_bytes,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={zip_filename}"
                }
            )
            
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                print(f"Cleaning up temporary directory: {temp_dir}")
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    print(f"Warning: Could not clean up temporary directory: {e}")
    
    except HTTPException:
        # Re-raise HTTP exceptions
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        # Clean up on error
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"Error exporting animation: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9010)
