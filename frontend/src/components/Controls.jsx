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
  cmap, setCmap,
  dpi, setDpi, 
  showScaleBar, setShowScaleBar,
  scaleBarSize, setScaleBarSize,
  scaleBarUnit, setScaleBarUnit
}) {
  return (
    <div className="controls-container">
      <div className="control-group compact">
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

      <div className="control-group compact">
        <label>Axis:</label>
        <select value={axis} onChange={(e) => setAxis(e.target.value)}>
          <option value="x">X</option>
          <option value="y">Y</option>
          <option value="z">Z</option>
        </select>
      </div>

      <div className="control-group compact">
        <label>Field:</label>
        <select value={field} onChange={(e) => setField(e.target.value)}>
          {fieldsList.map(f => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
      </div>

      <div className="control-group compact">
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

      <div className="control-group">
        <label>Limits (Min / Max):</label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem' }}>Min:</label>
            <input type="number" value={vmin} onChange={(e) => setVmin(e.target.value)} placeholder="Auto" />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem' }}>Max:</label>
            <input type="number" value={vmax} onChange={(e) => setVmax(e.target.value)} placeholder="Auto" />
          </div>
        </div>
      </div>

      <div className="control-group">
        <label>
          <input 
            type="checkbox" 
            checked={logScale} 
            onChange={(e) => setLogScale(e.target.checked)} 
            style={{ width: 'auto', marginRight: '0.5rem' }}
          />
          Log Scale
        </label>
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

          </div>
        )}
      </div>

      <div className="control-group">
        <label>
          <input 
            type="checkbox" 
            checked={showScaleBar} 
            onChange={(e) => setShowScaleBar(e.target.checked)} 
            style={{ width: 'auto', marginRight: '0.5rem' }}
          />
          Show Scale Bar
        </label>
        {showScaleBar && (
          <div style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem', display: 'block', marginBottom: '0.25rem' }}>
              Custom Size (optional):
            </label>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input 
                type="text" 
                value={scaleBarSize} 
                onChange={(e) => setScaleBarSize(e.target.value)} 
                placeholder="Auto"
                style={{ width: '80px' }}
              />
              <input 
                type="text" 
                value={scaleBarUnit} 
                onChange={(e) => setScaleBarUnit(e.target.value)} 
                placeholder="Unit"
                style={{ width: '60px' }}
              />
            </div>
          </div>
        )}
      </div>

      <div className="control-group compact">
        <label>DPI:</label>
        <input 
          type="number" 
          value={dpi} 
          onChange={(e) => setDpi(Number(e.target.value))}
          step="10"
        />
      </div>
      
      <button onClick={onRefresh}>Refresh</button>
    </div>
  );
}

export default Controls;
