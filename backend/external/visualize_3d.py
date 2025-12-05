#!/usr/bin/env python3
"""
3D Visualization of QUOKKA Simulation Data using YT
====================================================

This script demonstrates various 3D visualization techniques for QUOKKA
simulation data using the YT package. It creates volume renderings, 
isosurface plots, and interactive 3D visualizations.

Setup: source ~/rc/yt.rc before running this script.

Resolution Guide:
-----------------
Control rendering quality with the resolution parameter:

Resolution      Quality         Render Time     File Size    Use Case
-----------     -------         -----------     ---------    --------
(512, 512)      Low             ~10-20 sec      ~100 KB      Quick preview
(1024, 1024)    Standard        ~30-60 sec      ~300 KB      Default, good balance
(2048, 2048)    High            ~2-5 min        ~1 MB        Publication quality
(4096, 4096)    Very High       ~10-20 min      ~3 MB        High-end publications
(8192, 8192)    Ultra           ~30-60 min      ~10 MB       Posters, presentations

Example usage:
    create_volume_rendering(ds, field="density", resolution=(2048, 2048))
    create_rotating_volume_rendering(ds, field="density", resolution=(1024, 1024))
"""

import yt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import os

# set dpi to 600
import matplotlib
matplotlib.rcParams['savefig.dpi'] = 600

# Configuration
DATA_PATH = "data/plt348192"
OUTPUT_DIR = "output"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_dataset():
    """Load the QUOKKA simulation dataset."""
    print(f"Loading dataset from {DATA_PATH}...")
    ds = yt.load(DATA_PATH)
    print(f"Dataset loaded successfully!")
    print(f"Time: {ds.current_time}")
    print(f"Domain dimensions: {ds.domain_dimensions}")
    print(f"Domain width: {ds.domain_width}")
    print(f"\nAvailable fields:")
    for field in ds.field_list:
        print(f"  - {field}")
    return ds

def create_volume_rendering(ds, field="density", camera_dir=[1, 1, 1], width=1.0, resolution=(1024, 1024)):
    """
    Create a 3D volume rendering of the specified field.
    
    Parameters
    ----------
    ds : yt.Dataset
        The loaded dataset
    field : str
        The field to visualize (default: "density")
    camera_dir : list
        Camera viewing direction [x, y, z]
    width : float
        Width of the view in units of domain width
    resolution : tuple
        Resolution of the output image (width, height) in pixels
        Default: (1024, 1024). Use (2048, 2048) or (4096, 4096) for higher quality
    """
    print(f"\nCreating volume rendering for {field}...")
    
    # Create a scene
    sc = yt.create_scene(ds, field=("gas", field))
    
    # Get the source (volume rendering)
    source = sc[0]
    
    # Set up transfer function for better visualization
    # This maps data values to colors and opacities
    bounds = ds.all_data().quantities.extrema(("gas", field))
    print(f"Field bounds: {bounds}")
    
    # Use log scale for density
    real_bounds = np.log10(bounds)
    real_bounds[0] = real_bounds[1] - 8
    tf = yt.ColorTransferFunction(real_bounds)
    
    # Add multiple layers with different colors for depth perception
    nbins = 6
    tf.add_layers(nbins, w=0.02, colormap="inferno", alpha=np.logspace(-1, 0, nbins))
    
    source.tfh.tf = tf
    source.tfh.bounds = bounds
    source.tfh.set_log(True)
    
    # Set camera position for a good viewing angle
    cam = sc.camera
    
    # Set camera resolution for higher quality rendering
    cam.resolution = resolution
    print(f"   Camera resolution: {resolution[0]} x {resolution[1]} pixels")
    
    # Set orientation: z is up, y is right
    # Normalize camera direction
    view_dir = np.array(camera_dir, dtype=float)
    view_dir = view_dir / np.linalg.norm(view_dir)
    
    # Set north vector (up direction) - use z unless looking along z
    if abs(view_dir[2]) > 0.9:  # Looking along z-axis
        north = np.array([0, 1, 0])
    else:  # For other views, z is up
        north = np.array([0, 0, 1])
    
    # Calculate camera position
    cam_pos = ds.domain_center + 1.5 * width * ds.domain_width * view_dir
    
    # Set camera orientation properly using switch_orientation
    cam.switch_orientation(normal_vector=view_dir, north_vector=north)
    cam.set_position(cam_pos)
    cam.set_focus(ds.domain_center)
    cam.set_width(width * ds.domain_width)
    
    # Render and save
    output_file = f"{OUTPUT_DIR}/volume_render_{field}.png"
    sc.save(output_file, sigma_clip=4.0)
    print(f"Volume rendering saved to {output_file}")
    
    return sc

def create_rotating_volume_rendering(ds, field="density", n_frames=36, width=1.0, resolution=(1024, 1024)):
    """
    Create a rotating volume rendering animation.
    
    Parameters
    ----------
    ds : yt.Dataset
        The loaded dataset
    field : str
        The field to visualize
    n_frames : int
        Number of frames for 360-degree rotation
    width : float
        Width of the view in units of domain width
    resolution : tuple
        Resolution of the output image (width, height) in pixels
        Default: (1024, 1024). Use (2048, 2048) or higher for better quality
    """
    print(f"\nCreating rotating volume rendering for {field}...")
    
    sc = yt.create_scene(ds, field=("gas", field))
    source = sc[0]
    
    # Set up transfer function
    bounds = ds.all_data().quantities.extrema(("gas", field))
    tf = yt.ColorTransferFunction(np.log10(bounds))
    tf.add_layers(5, w=0.02, colormap="viridis", alpha=np.logspace(-1, 0, 5))
    source.tfh.tf = tf
    source.tfh.bounds = bounds
    source.tfh.set_log(True)
    
    # Set camera with fixed north vector (z is up)
    cam = sc.camera
    cam.resolution = resolution
    print(f"   Camera resolution: {resolution[0]} x {resolution[1]} pixels")
    
    north = np.array([0, 0, 1])  # Keep z as up direction throughout rotation
    
    # Initial camera setup
    cam.set_width(width * ds.domain_width)
    cam.set_focus(ds.domain_center)
    
    # Create rotation frames
    print(f"Rendering {n_frames} frames...")
    radius = 1.5 * width
    
    for i in range(n_frames):
        # Calculate camera position rotating around z-axis
        angle = 2 * np.pi * i / n_frames
        
        # Camera position in cylindrical coordinates (rotating in xy-plane)
        # Use the domain_width components to maintain units
        cam_offset_x = radius * ds.domain_width[0] * np.cos(angle)
        cam_offset_y = radius * ds.domain_width[1] * np.sin(angle)
        cam_offset_z = 0.5 * radius * ds.domain_width[2]  # Slight elevation for better 3D view
        
        cam_pos = ds.domain_center + [cam_offset_x, cam_offset_y, cam_offset_z]
        
        # Calculate viewing direction (unitless)
        view_dir = (ds.domain_center - cam_pos).to_ndarray()
        view_dir = view_dir / np.linalg.norm(view_dir)
        
        # Set camera orientation with fixed north vector
        cam.switch_orientation(normal_vector=view_dir, north_vector=north)
        cam.set_position(cam_pos)
        
        output_file = f"{OUTPUT_DIR}/rotation_{field}_{i:03d}.png"
        sc.save(output_file, sigma_clip=4.0)
        print(f"  Frame {i+1}/{n_frames} saved")
    
    print(f"Rotation frames saved. Create animation with:")
    print(f"  ffmpeg -framerate 10 -i {OUTPUT_DIR}/rotation_{field}_%03d.png "
          f"-c:v libx264 -pix_fmt yuv420p {OUTPUT_DIR}/rotation_{field}.mp4")

def create_isosurface_rendering(ds, field="density", n_contours=3):
    """
    Create an isosurface rendering showing surfaces of constant field value.
    
    Parameters
    ----------
    ds : yt.Dataset
        The loaded dataset
    field : str
        The field to visualize
    n_contours : int
        Number of isosurface levels
    """
    print(f"\nCreating isosurface rendering for {field}...")
    
    # Create scene
    sc = yt.Scene()
    
    # Add volume source for context
    vol_source = yt.VolumeSource(ds, field=("gas", field))
    bounds = ds.all_data().quantities.extrema(("gas", field))
    
    # Make volume semi-transparent for context
    tf = yt.ColorTransferFunction(np.log10(bounds))
    tf.add_layers(3, w=0.01, colormap="Blues", alpha=np.logspace(-2, -1, 3))
    vol_source.tfh.tf = tf
    vol_source.tfh.bounds = bounds
    vol_source.tfh.set_log(True)
    sc.add_source(vol_source)
    
    # Add isosurface contours
    min_val, max_val = bounds
    contour_values = np.logspace(np.log10(min_val), np.log10(max_val), n_contours+2)[1:-1]
    
    colors = plt.cm.plasma(np.linspace(0.2, 0.8, n_contours))
    
    for i, (value, color) in enumerate(zip(contour_values, colors)):
        print(f"  Adding isosurface at value {value:.2e}")
        surf = ds.surface(ds.all_data(), ("gas", field), value)
        iso_source = yt.MeshSource(surf, color=color[:3])
        sc.add_source(iso_source)
    
    # Set up camera
    cam = sc.add_camera(ds)
    cam.set_width(ds.domain_width)
    cam.position = ds.domain_center + 1.5 * ds.domain_width
    cam.focus = ds.domain_center
    
    # Render
    output_file = f"{OUTPUT_DIR}/isosurface_{field}.png"
    sc.save(output_file, sigma_clip=4.0)
    print(f"Isosurface rendering saved to {output_file}")

def create_multifield_rendering(ds):
    """
    Create a multi-panel figure showing different fields.
    
    Parameters
    ----------
    ds : yt.Dataset
        The loaded dataset
    """
    print("\nCreating multi-field rendering...")
    
    fields = ["density", "internal_energy_density"]
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for ax, field in zip(axes, fields):
        print(f"  Rendering {field}...")
        
        # Create a projection plot
        p = yt.ProjectionPlot(ds, "z", ("gas", field))
        p.set_log(("gas", field), True)
        p.set_cmap(("gas", field), "viridis")
        
        # Get the plot and display it
        plot = p.plots[("gas", field)]
        plot.figure = fig
        plot.axes = ax
        p._setup_plots()
        
        ax.set_title(field, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    output_file = f"{OUTPUT_DIR}/multifield_projection.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Multi-field rendering saved to {output_file}")
    plt.close()

def create_3d_slice_rendering(ds, field="density"):
    """
    Create a 3D rendering with orthogonal slice planes.
    
    Parameters
    ----------
    ds : yt.Dataset
        The loaded dataset
    field : str
        The field to visualize
    """
    print(f"\nCreating 3D slice rendering for {field}...")
    
    # Create scene
    sc = yt.Scene()
    
    # Add three orthogonal slices
    for normal, color in zip(['x', 'y', 'z'], ['r', 'g', 'b']):
        print(f"  Adding {normal}-slice...")
        
        # Create slice at domain center
        slc = ds.slice(normal, ds.domain_center[['xyz'.index(normal)]])
        
        # Create a plane mesh from the slice
        # Note: This is a simplified approach; actual implementation may vary
        slice_source = yt.SliceSource(ds, normal, ("gas", field))
        sc.add_source(slice_source)
    
    # Set up camera
    cam = sc.add_camera(ds)
    cam.set_width(ds.domain_width * 1.5)
    cam.position = ds.domain_center + 2.0 * ds.domain_width
    cam.focus = ds.domain_center
    
    # Render
    output_file = f"{OUTPUT_DIR}/3d_slices_{field}.png"
    sc.save(output_file, sigma_clip=4.0)
    print(f"3D slice rendering saved to {output_file}")

def analyze_dataset(ds):
    """
    Perform basic analysis and print statistics.
    
    Parameters
    ----------
    ds : yt.Dataset
        The loaded dataset
    """
    print("\n" + "="*60)
    print("DATASET ANALYSIS")
    print("="*60)
    
    ad = ds.all_data()
    
    fields_to_analyze = ["density", "internal_energy_density"]
    
    for field in fields_to_analyze:
        print(f"\n{field}:")
        field_tuple = ("gas", field)
        
        min_val = ad.min(field_tuple)
        max_val = ad.max(field_tuple)
        mean_val = ad.mean(field_tuple)
        
        print(f"  Min:  {min_val:.4e}")
        print(f"  Max:  {max_val:.4e}")
        print(f"  Mean: {mean_val:.4e}")
        print(f"  Range: {max_val/min_val:.2e}x")

def main():
    """Main execution function."""
    print("="*60)
    print("3D VISUALIZATION OF QUOKKA SIMULATION DATA")
    print("="*60)
    
    # Load dataset
    ds = load_dataset()
    
    # Analyze dataset
    analyze_dataset(ds)
    
    # Create various visualizations
    print("\n" + "="*60)
    print("CREATING VISUALIZATIONS")
    print("="*60)

    # High-resolution rendering examples:
    # Resolution options:
    #   (1024, 1024)  - Default, fast
    #   (2048, 2048)  - High quality
    #   (4096, 4096)  - Very high quality (slow)
    #   (8192, 8192)  - Ultra high quality (very slow)
    
    create_volume_rendering(ds, field="density", camera_dir=[1, 0, 0], width=4.0, 
                           resolution=(2048, 2048))
    
    # 1. Basic volume rendering
    # create_volume_rendering(ds, field="density", resolution=(2048, 2048))
    
    # 2. Volume rendering for temperature
    # create_volume_rendering(ds, field="temperature", resolution=(2048, 2048))
    
    # 3. Isosurface rendering
    # create_isosurface_rendering(ds, field="density", n_contours=3)
    
    # 4. Multi-field projection
    # create_multifield_rendering(ds)
    
    # 5. 3D slices (optional - comment out if too slow)
    # create_3d_slice_rendering(ds, field="density")
    
    # 6. Rotating animation (optional - creates many frames)
    # Uncomment to create rotation animation:
    # create_rotating_volume_rendering(ds, field="density", n_frames=36, width=1.0,
    #                                  resolution=(1024, 1024))
    
    print("\n" + "="*60)
    print("VISUALIZATION COMPLETE!")
    print("="*60)
    print(f"\nAll outputs saved to: {OUTPUT_DIR}/")
    print("\nGenerated files:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith('.png'):
            print(f"  - {OUTPUT_DIR}/{f}")

if __name__ == "__main__":
    main()

