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
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm

from fastapi.middleware.cors import CORSMiddleware

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
    data_dir = "data"
    if not os.path.exists(data_dir):
        return {"datasets": []}
    
    datasets = [d for d in os.listdir(data_dir) if d.startswith("plt") and os.path.isdir(os.path.join(data_dir, d))]
    datasets.sort()
    return {"datasets": datasets}

@app.post("/api/load_dataset")
def load_dataset(filename: str = "plt00500"):
    global ds
    path = os.path.join("data", filename)
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
    resolution: int = 512,
    show_scale_bar: bool = False,
    scale_bar_size: Optional[float] = None,
    scale_bar_unit: Optional[str] = None
):
    global ds
    if ds is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
    
    # Debug logging
    import sys
    print(f"DEBUG: scale_bar_size={scale_bar_size}, scale_bar_unit={scale_bar_unit}, show_scale_bar={show_scale_bar}")
    sys.stdout.flush()
    
    try:
        if coord is None:
            coord = ds.domain_center[ds.coordinates.axis_id[axis]]
        
        slc = yt.SlicePlot(ds, axis, ("boxlib", field), center=ds.domain_center)
        
        # Calculate aspect ratio and set buffer size
        axis_id = ds.coordinates.axis_id[axis]
        x_ax_id = ds.coordinates.x_axis[axis_id]
        y_ax_id = ds.coordinates.y_axis[axis_id]
        
        Wx = ds.domain_width[x_ax_id].v
        Wy = ds.domain_width[y_ax_id].v
        aspect = float(Wy / Wx)
        
        
        if aspect > 1:
            nx = resolution
            ny = int(resolution * aspect)
        else:
            ny = resolution
            nx = int(resolution / aspect)
            
        slc.set_buff_size((nx, ny))
        
        frb = slc.frb
        image_data = np.array(frb[("boxlib", field)])
        
        buf = io.BytesIO()
        
        if show_colorbar:
            # Use matplotlib figure to show colorbar
            # Calculate figure size based on actual image dimensions to preserve aspect ratio
            base_width = 8  # inches
            fig_aspect = ny / nx  # actual image aspect ratio
            fig_height = base_width * fig_aspect
            
            fig = plt.figure(figsize=(base_width, fig_height))
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
                    # Try to get the default label from yt field info
                    label = ds.field_info[("boxlib", field)].get_label()
                except:
                    label = field
            
            cbar.set_label(label)
            
            # Add scale bar if requested
            if show_scale_bar:
                print(f"DEBUG: Inside show_scale_bar block")
                # Get axis information
                axis_id = ds.coordinates.axis_id[axis]
                x_ax_id = ds.coordinates.x_axis[axis_id]
                domain_width = ds.domain_width[x_ax_id]
                
                print(f"DEBUG: domain_width={domain_width}")
                print(f"DEBUG: scale_bar_size={scale_bar_size}, scale_bar_unit={scale_bar_unit}")
                print(f"DEBUG: Condition check: {scale_bar_size is not None and scale_bar_unit is not None}")
                
                # Use custom scale bar size if provided, otherwise auto-calculate
                if scale_bar_size is not None and scale_bar_unit is not None:
                    print(f"DEBUG: Using custom scale bar")
                    # Convert custom unit to box length (fraction of domain width) using yt.YTQuantity
                    try:
                        # Create a YTQuantity from the user input
                        custom_quantity = yt.YTQuantity(scale_bar_size, scale_bar_unit)
                        print(f"DEBUG: Created custom_quantity: {custom_quantity}")
                        
                        # Convert to fraction of domain width (box length units)
                        # This is the key: divide by domain_width to get normalized units
                        box_length_fraction = float(custom_quantity / domain_width)
                        print(f"DEBUG: box_length_fraction: {box_length_fraction}")
                        
                        # Display label uses the user's specified unit
                        display_label = f'{scale_bar_size:.3g} {scale_bar_unit}'
                        print(f"DEBUG: display_label={display_label}")
                    except Exception as e:
                        # If conversion fails, fall back to auto-calculation
                        print(f"Warning: Could not convert {scale_bar_size} {scale_bar_unit}: {e}")
                        import traceback
                        traceback.print_exc()
                        box_length_fraction = 0.2  # Default to 1/5 of domain
                        display_label = f'{0.2 * float(domain_width.v):.3g} {domain_width.units}'
                else:
                    print(f"DEBUG: Using auto-calculated scale bar")
                    # Auto-calculate: 1/5 of domain width
                    box_length_fraction = 0.2
                    scale_value = 0.2 * float(domain_width.v)
                    
                    # Round to a nice number
                    magnitude = 10 ** np.floor(np.log10(scale_value))
                    nice_scale = np.round(scale_value / magnitude) * magnitude
                    
                    # Recalculate box_length_fraction with the rounded value
                    box_length_fraction = nice_scale / float(domain_width.v)
                    display_label = f'{nice_scale:.3g} {domain_width.units}'
                    print(f"DEBUG: Auto box_length_fraction={box_length_fraction}, display_label={display_label}")
                
                # Convert box length fraction to pixel size
                # The image has nx pixels spanning the full domain (box length = 1.0)
                scale_bar_pixels = box_length_fraction * nx
                print(f"DEBUG: scale_bar_pixels={scale_bar_pixels}")
                
                # Create scale bar
                fontprops = fm.FontProperties(size=10, weight='bold')
                scalebar = AnchoredSizeBar(
                    ax.transData,
                    scale_bar_pixels,
                    display_label,
                    'lower left',
                    pad=0.5,
                    color='white',
                    frameon=False,
                    size_vertical=scale_bar_pixels/50,
                    fontproperties=fontprops
                )
                ax.add_artist(scalebar)
            
            ax.axis('off')
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
            plt.close(fig)
        else:
            # Save directly using imsave to preserve aspect ratio and avoid borders
            # imsave doesn't support 'norm' directly, so we apply it manually
            norm = matplotlib.colors.LogNorm(vmin=vmin, vmax=vmax) if log_scale else matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
            
            # Map data to 0-1 using the norm
            # We need to handle cases where data might be <= 0 for LogNorm if vmin is not set
            # But matplotlib's LogNorm usually handles this by masking or clipping if we are careful.
            # However, calling norm(data) directly might return masked array.
            
            mapped_data = norm(image_data)
            
            # Apply colormap
            cm = matplotlib.colormaps[cmap]
            colored_data = cm(mapped_data)
            
            # If scale bar is requested, we need to use matplotlib figure instead of imsave
            if show_scale_bar:
                # Calculate aspect ratio for figure
                axis_id = ds.coordinates.axis_id[axis]
                x_ax_id = ds.coordinates.x_axis[axis_id]
                y_ax_id = ds.coordinates.y_axis[axis_id]
                Wx = ds.domain_width[x_ax_id].v
                Wy = ds.domain_width[y_ax_id].v
                aspect = float(Wy / Wx)
                
                # Calculate figure size based on actual image dimensions to preserve aspect ratio
                # Use a base width and calculate height from the image aspect ratio
                base_width = 8  # inches
                fig_aspect = ny / nx  # actual image aspect ratio
                fig_height = base_width * fig_aspect
                
                fig = plt.figure(figsize=(base_width, fig_height))
                ax = fig.add_subplot(111)
                ax.imshow(colored_data, origin='lower', aspect='auto')
                
                # Get scale bar size and unit
                axis_id = ds.coordinates.axis_id[axis]
                x_ax_id = ds.coordinates.x_axis[axis_id]
                domain_width = ds.domain_width[x_ax_id]
                
                # Use custom scale bar size if provided, otherwise auto-calculate
                if scale_bar_size is not None and scale_bar_unit is not None:
                    # Convert custom unit to box length (fraction of domain width) using yt.YTQuantity
                    try:
                        custom_quantity = yt.YTQuantity(scale_bar_size, scale_bar_unit)
                        box_length_fraction = float(custom_quantity / domain_width)
                        display_label = f'{scale_bar_size:.3g} {scale_bar_unit}'
                    except Exception as e:
                        print(f"Warning: Could not convert {scale_bar_size} {scale_bar_unit}: {e}")
                        box_length_fraction = 0.2
                        display_label = f'{0.2 * float(domain_width.v):.3g} {domain_width.units}'
                else:
                    # Auto-calculate: 1/5 of domain width
                    box_length_fraction = 0.2
                    scale_value = 0.2 * float(domain_width.v)
                    
                    # Round to a nice number
                    magnitude = 10 ** np.floor(np.log10(scale_value))
                    nice_scale = np.round(scale_value / magnitude) * magnitude
                    
                    # Recalculate box_length_fraction with the rounded value
                    box_length_fraction = nice_scale / float(domain_width.v)
                    display_label = f'{nice_scale:.3g} {domain_width.units}'
                
                # Convert box length fraction to pixel size
                scale_bar_pixels = box_length_fraction * nx
                
                # Create scale bar
                fontprops = fm.FontProperties(size=10, weight='bold')
                scalebar = AnchoredSizeBar(
                    ax.transData,
                    scale_bar_pixels,
                    display_label,
                    'lower left',
                    pad=0.5,
                    color='white',
                    frameon=False,
                    size_vertical=scale_bar_pixels/50,
                    fontproperties=fontprops
                )
                ax.add_artist(scalebar)
                
                ax.axis('off')
                plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
                plt.close(fig)
            else:
                plt.imsave(buf, colored_data, origin='lower', format='png', pil_kwargs={'dpi': (300, 300)})
            
        buf.seek(0)
        
        return Response(content=buf.getvalue(), media_type="image/png")

    except Exception as e:
        print(f"Error generating slice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
