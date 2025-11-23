import React from 'react';

function Controls({ 
  axis, setAxis, 
  field, setField, 
  fieldsList, 
  coord, setCoord,
  onRefresh,
  datasets, currentDataset, setDataset,
  isPlaying, setIsPlaying,
  fps, setFps,
  showColorbar, setShowColorbar,
  vmin, setVmin,
  vmax, setVmax,
  logScale, setLogScale,
  colorbarLabel, setColorbarLabel,
  colorbarOrientation, setColorbarOrientation,
  cmap, setCmap
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

          <div className="fps-buttons">
            {[1, 3, 5, 10, 15, 30].map(val => (
              <button 
                key={val} 
                onClick={() => setFps(val)}
                className={fps === val ? 'active' : ''}
              >
                {val}
              </button>
            ))}
          </div>
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
        <label>
          <input 
            type="checkbox" 
            checked={showColorbar} 
            onChange={(e) => setShowColorbar(e.target.checked)} 
            style={{ width: 'auto', marginRight: '0.5rem' }}
          />
          Show Colorbar
        </label>
        <label style={{ marginTop: '0.5rem' }}>
          <input 
            type="checkbox" 
            checked={logScale} 
            onChange={(e) => setLogScale(e.target.checked)} 
            style={{ width: 'auto', marginRight: '0.5rem' }}
          />
          Log Scale
        </label>
        {showColorbar && (
          <div style={{ marginTop: '0.5rem' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem' }}>Label:</label>
            <input 
              type="text" 
              value={colorbarLabel} 
              onChange={(e) => setColorbarLabel(e.target.value)} 
              placeholder="Default"
              style={{ marginTop: '0.2rem' }}
            />
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem', marginTop: '0.5rem', display: 'block' }}>Position:</label>
            <select 
              value={colorbarOrientation} 
              onChange={(e) => setColorbarOrientation(e.target.value)}
              style={{ marginTop: '0.2rem' }}
            >
              <option value="right">Right</option>
              <option value="top">Top</option>
            </select>
          </div>
        )}
      </div>

      <div className="control-group">
        <label>Limits (Min / Max):</label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input 
            type="text" 
            value={vmin} 
            onChange={(e) => setVmin(e.target.value)} 
            placeholder="Min"
          />
          <input 
            type="text" 
            value={vmax} 
            onChange={(e) => setVmax(e.target.value)} 
            placeholder="Max"
          />
        </div>
      </div>

      <div className="control-group">
        <label>Field:</label>
        <select value={field} onChange={(e) => setField(e.target.value)}>
          {fieldsList.map(f => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
      </div>

      <div className="control-group">
        <label>Colormap:</label>
        <select value={cmap} onChange={(e) => setCmap(e.target.value)}>
          <option value="viridis">Viridis</option>
          <option value="plasma">Plasma</option>
          <option value="inferno">Inferno</option>
          <option value="magma">Magma</option>
          <option value="cividis">Cividis</option>
          <option value="coolwarm">Coolwarm</option>
          <option value="RdBu">RdBu</option>
          <option value="seismic">Seismic</option>
          <option value="jet">Jet</option>
          <option value="hot">Hot</option>
          <option value="gray">Gray</option>
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
