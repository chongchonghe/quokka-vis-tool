import React, { useState, useEffect } from 'react';

function Viewer({ axis, field, coord, refreshTrigger, showColorbar, vmin, vmax, logScale, colorbarLabel, colorbarOrientation, colormap }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (field) {
      fetchImage();
    }
  }, [axis, field, coord, refreshTrigger, showColorbar, vmin, vmax, logScale, colorbarLabel, colorbarOrientation, colormap]);

  const fetchImage = async () => {
    setError(null);
    try {
      let url = `http://localhost:8000/api/slice?axis=${axis}&field=${field}&show_colorbar=${showColorbar}&log_scale=${logScale}`;
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
      if (colormap) {
        url += `&colormap=${colormap}`;
      }
      
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
