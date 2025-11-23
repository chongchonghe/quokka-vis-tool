from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
import yt
import os
from typing import List, Optional
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

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
    return {"message": "AMReX Viz Tool Backend"}

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
    colorbar_label: Optional[str] = None
):
    global ds
    if ds is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
    
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
        
        resolution = 800
        if aspect > 1:
            ny = resolution
            nx = int(resolution / aspect)
        else:
            nx = resolution
            ny = int(resolution * aspect)
            
        slc.set_buff_size((nx, ny))
        
        frb = slc.frb
        image_data = np.array(frb[("boxlib", field)])
        
        buf = io.BytesIO()
        
        if show_colorbar:
            # Use matplotlib figure to show colorbar
            fig = plt.figure(figsize=(8, 8/aspect if aspect < 1 else 8))
            ax = fig.add_subplot(111)
            
            norm = matplotlib.colors.LogNorm(vmin=vmin, vmax=vmax) if log_scale else matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
            
            im = ax.imshow(image_data, origin='lower', cmap='viridis', norm=norm)
            cbar = fig.colorbar(im, ax=ax)
            
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
            
            ax.axis('off')
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
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
            cm = matplotlib.colormaps['viridis']
            colored_data = cm(mapped_data)
            
            plt.imsave(buf, colored_data, origin='lower', format='png')
            
        buf.seek(0)
        
        return Response(content=buf.getvalue(), media_type="image/png")

    except Exception as e:
        print(f"Error generating slice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
