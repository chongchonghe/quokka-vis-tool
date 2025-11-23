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
    coord: Optional[float] = None
):
    global ds
    if ds is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
    
    try:
        if coord is None:
            coord = ds.domain_center[ds.coordinates.axis_id[axis]]
        
        # field comes in as just the name, e.g. "gasDensity"
        # we assume it's a boxlib field
        slc = yt.SlicePlot(ds, axis, ("boxlib", field), center=ds.domain_center)
        # We might want to set the center to the specific coordinate if provided, 
        # but SlicePlot takes 'center' as the center of the plot window. 
        # To slice at a specific coordinate along the normal, we usually pass it as the third arg to SlicePlot 
        # OR we can just use the default center which usually cuts through the middle.
        # For now, let's stick to simple center slice.
        
        # Convert to image buffer
        # This is a bit hacky to get the raw image data out quickly for a prototype
        # Ideally we'd use frb (Fixed Resolution Buffer)
        
        frb = slc.frb
        image_data = np.array(frb[("boxlib", field)])
        
        # Normalize and colorize using matplotlib
        plt.figure(figsize=(8, 8))
        plt.imshow(image_data, origin='lower', cmap='viridis')
        plt.axis('off')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        plt.close()
        buf.seek(0)
        
        return Response(content=buf.getvalue(), media_type="image/png")

    except Exception as e:
        print(f"Error generating slice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
