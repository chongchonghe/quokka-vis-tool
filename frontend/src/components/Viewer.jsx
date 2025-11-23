import React, { useState, useEffect } from 'react';

function Viewer({ axis, field, coord, refreshTrigger }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchImage();
  }, [axis, field, coord, refreshTrigger]);

  const fetchImage = async () => {
    setLoading(true);
    setError(null);
    try {
      let url = `http://localhost:8000/api/slice?axis=${axis}&field=${field}`;
      if (coord !== null) {
        url += `&coord=${coord}`;
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
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="viewer-container">
      {loading && <div className="loading">Loading...</div>}
      {error && <div className="error">{error}</div>}
      {imageUrl && <img src={imageUrl} alt="Slice" className="slice-image" />}
    </div>
  );
}

export default Viewer;
