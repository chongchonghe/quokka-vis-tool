import React, { useState, useEffect } from 'react';

function Viewer({ 
  axis, field, coord, refreshTrigger, 
  showColorbar, vmin, vmax, logScale, colorbarLabel, colorbarOrientation, cmap, 
  showScaleBar, scaleBarSize, scaleBarUnit, 
  dpi,
  // New props
  plotType, weightField, widthValue, widthUnit, particles, particleSize, particleColor, grids, timestamp, topLeftText, topRightText
}) {
  const [imageUrl, setImageUrl] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (field) {
      fetchImage();
    }
  }, [
    axis, field, coord, refreshTrigger, 
    showColorbar, vmin, vmax, logScale, colorbarLabel, colorbarOrientation, cmap,
    showScaleBar, scaleBarSize, scaleBarUnit, dpi,
    plotType, weightField, widthValue, widthUnit, particles, particleSize, particleColor, grids, timestamp, topLeftText, topRightText
  ]);

  const fetchImage = async () => {
    setError(null);
    try {
      let url = `/api/slice?axis=${axis}&field=${field}&refreshTrigger=${refreshTrigger}&show_colorbar=${showColorbar}&log_scale=${logScale}&cmap=${cmap}&dpi=${dpi || 300}&show_scale_bar=${showScaleBar}`;
      if (coord !== null) {
        url += `&coord=${coord}`;
      }
      if (vmin) {
        url += `&vmin=${vmin}`;
      }
      if (vmax) {
        url += `&vmax=${vmax}`;
      }
      if (colorbarLabel) {
        url += `&colorbar_label=${encodeURIComponent(colorbarLabel)}`;
      }
      if (colorbarOrientation) {
        url += `&colorbar_orientation=${colorbarOrientation}`;
      }
      
      if (scaleBarSize && scaleBarSize !== '') {
        url += `&scale_bar_size=${parseFloat(scaleBarSize)}`;
      }
      if (scaleBarUnit && scaleBarUnit !== '') {
        url += `&scale_bar_unit=${encodeURIComponent(scaleBarUnit)}`;
      }

      // New params
      if (plotType) url += `&kind=${plotType}`;
      if (weightField && weightField !== 'None') url += `&weight_field=${weightField}`;
      if (widthValue) url += `&width_value=${widthValue}`;
      if (widthUnit) url += `&width_unit=${widthUnit}`;
      if (particles) url += `&particles=${encodeURIComponent(particles)}`;
      if (particleSize) url += `&particle_size=${particleSize}`;
      if (particleColor) url += `&particle_color=${encodeURIComponent(particleColor)}`;
      if (grids) url += `&grids=true`;
      if (timestamp) url += `&timestamp=true`;
      if (topLeftText) url += `&top_left_text=${encodeURIComponent(topLeftText)}`;
      if (topRightText) url += `&top_right_text=${encodeURIComponent(topRightText)}`;
      
      console.log('DEBUG Viewer: Final URL:', url);
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch slice');
      }
      
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      setImageUrl(objectUrl);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="viewer-container" style={{ position: 'relative' }}>
      {imageUrl && <img src={imageUrl} alt="Slice" className="slice-image" />}
      {error && (
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(244, 67, 54, 0.95)',
          color: 'white',
          padding: '12px 24px',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          zIndex: 1000,
          maxWidth: '80%',
          textAlign: 'center',
          fontSize: '14px',
          fontWeight: '500'
        }}>
          {error}
        </div>
      )}
    </div>
  );
}

export default Viewer;
