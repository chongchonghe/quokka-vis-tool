import React from 'react';

function Controls({ 
  axis, setAxis, 
  field, setField, 
  fieldsList, 
  coord, setCoord,
  onRefresh 
}) {
  return (
    <div className="controls-container">
      <div className="control-group">
        <label>Axis:</label>
        <select value={axis} onChange={(e) => setAxis(e.target.value)}>
          <option value="x">X</option>
          <option value="y">Y</option>
          <option value="z">Z</option>
        </select>
      </div>

      <div className="control-group">
        <label>Field:</label>
        <select value={field} onChange={(e) => setField(e.target.value)}>
          {fieldsList.map(f => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
      </div>

      {/* 
      <div className="control-group">
        <label>Coordinate:</label>
        <input 
          type="number" 
          step="0.01"
          value={coord || ''} 
          onChange={(e) => setCoord(e.target.value ? parseFloat(e.target.value) : null)} 
          placeholder="Center"
        />
      </div>
      */}
      
      <button onClick={onRefresh}>Refresh</button>
    </div>
  );
}

export default Controls;
