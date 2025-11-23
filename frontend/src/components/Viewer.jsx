import React, { useState, useEffect } from 'react';

function Viewer({ axis, field, coord, refreshTrigger, showColorbar, vmin, vmax, logScale, colorbarLabel, colorbarOrientation, cmap, resolution, showScaleBar, scaleBarSize, scaleBarUnit }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (field) {
      fetchImage();
    }
  }, [axis, field, coord, refreshTrigger, showColorbar, vmin, vmax, logScale, colorbarLabel, colorbarOrientation, cmap, resolution, showScaleBar, scaleBarSize, scaleBarUnit]);

  const fetchImage = async () => {
    setError(null);
    try {
      let url = `http://localhost:8000/api/slice?axis=${axis}&field=${field}&show_colorbar=${showColorbar}&log_scale=${logScale}&cmap=${cmap}&resolution=${resolution}&show_scale_bar=${showScaleBar}`;
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
      
      console.log('DEBUG Viewer: scaleBarSize=', scaleBarSize, 'scaleBarUnit=', scaleBarUnit);
      
      if (scaleBarSize && scaleBarSize !== '') {
        console.log('DEBUG Viewer: Adding scale_bar_size to URL:', parseFloat(scaleBarSize));
        url += `&scale_bar_size=${parseFloat(scaleBarSize)}`;
      }
      if (scaleBarUnit && scaleBarUnit !== '') {
        console.log('DEBUG Viewer: Adding scale_bar_unit to URL:', scaleBarUnit);
        url += `&scale_bar_unit=${encodeURIComponent(scaleBarUnit)}`;
      }
      
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
    <div className="viewer-container">
      {error && <div className="error">{error}</div>}
      {imageUrl && <img src={imageUrl} alt="Slice" className="slice-image" />}
    </div>
  );
}

export default Viewer;
