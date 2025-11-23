import React from 'react';

function Controls({ 
  axis, setAxis, 
  field, setField, 
  fieldsList, 
  coord, setCoord,
  onRefresh,
  datasets, currentDataset, setDataset,
  isPlaying, setIsPlaying,
  animationSpeed, setAnimationSpeed
}) {
  return (
    <div className="controls-container">
      <div className="control-group">
        <label>Dataset:</label>
        <select value={currentDataset} onChange={(e) => setDataset(e.target.value)}>
          {datasets.map(d => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      <div className="control-group">
        <label>Animation:</label>
        <div className="animation-controls">
          <button onClick={() => setIsPlaying(!isPlaying)}>
            {isPlaying ? 'Pause' : 'Play'}
          </button>
          <input 
            type="range" 
            min="100" 
            max="2000" 
            step="100"
            value={animationSpeed} 
            onChange={(e) => setAnimationSpeed(Number(e.target.value))}
          />
          <span>{animationSpeed}ms</span>
        </div>
      </div>

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
