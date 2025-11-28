import React, { useState } from 'react';

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
  scaleBarUnit, setScaleBarUnit,
  // New props
  plotType, setPlotType,
  weightField, setWeightField,
  widthValue, setWidthValue,
  widthUnit, setWidthUnit,
  particles, setParticles,
  particleTypes,
  particleSize, setParticleSize,
  particleColor, setParticleColor,
  grids, setGrids,
  timestamp, setTimestamp,
  topLeftText, setTopLeftText,
  topRightText, setTopRightText,
  // Export props
  onExportCurrentFrame,
  onExportAnimation,
  isExporting,
  exportProgress,
  exportFps,
  setExportFps
}) {
  const [particlesExpanded, setParticlesExpanded] = useState(false);

  const handleParticleToggle = (particleType) => {
    if (particles.includes(particleType)) {
      setParticles(particles.filter(p => p !== particleType));
    } else {
      setParticles([...particles, particleType]);
    }
  };
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
        <label>Plot Type:</label>
        <select value={plotType} onChange={(e) => setPlotType(e.target.value)}>
          <option value="slc">Slice</option>
          <option value="prj">Projection</option>
        </select>
      </div>

      {plotType === 'prj' && (
        <div className="control-group compact">
          <label>Weight Field:</label>
          <select value={weightField} onChange={(e) => setWeightField(e.target.value)}>
            <option value="None">None</option>
            <option value="density">Density</option>
            <option value="cell_volume">Cell Volume</option>
            <option value="cell_mass">Cell Mass</option>
          </select>
        </div>
      )}

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
        <label>Width:</label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ flex: 1 }}>
             <input type="number" value={widthValue} onChange={(e) => setWidthValue(e.target.value)} placeholder="Full" />
          </div>
          <div style={{ flex: 1 }}>
             <input type="text" value={widthUnit} onChange={(e) => setWidthUnit(e.target.value)} placeholder="Unit (e.g. kpc)" />
          </div>
        </div>
      </div>

      <div className="control-group">
        <label 
          onClick={() => setParticlesExpanded(!particlesExpanded)}
          style={{ 
            cursor: 'pointer', 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            userSelect: 'none'
          }}
        >
          <span>Particles {particles.length > 0 && `(${particles.length})`}</span>
          <span style={{ fontSize: '0.8rem' }}>{particlesExpanded ? '▼' : '▶'}</span>
        </label>
        {particlesExpanded && (
          <div style={{ 
            marginTop: '0.5rem',
            paddingLeft: '0.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}>
            <div style={{ 
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              paddingBottom: '0.5rem',
              borderBottom: '1px solid #ddd'
            }}>
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <label style={{ fontWeight: 'normal', fontSize: '0.9rem', minWidth: '80px' }}>
                  Marker Size:
                </label>
                <input 
                  type="number" 
                  className="with-spinner"
                  value={particleSize}
                  onChange={(e) => setParticleSize(Number(e.target.value))}
                  min="1"
                  max="20"
                  style={{ width: '70px' }}
                />
              </div>
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <label style={{ fontWeight: 'normal', fontSize: '0.9rem', minWidth: '80px' }}>
                  Marker Color:
                </label>
                <select 
                  value={particleColor}
                  onChange={(e) => setParticleColor(e.target.value)}
                  style={{ flex: 1 }}
                >
                  <option value="red">Red</option>
                  <option value="white">White</option>
                  <option value="black">Black</option>
                  <option value="yellow">Yellow</option>
                  <option value="cyan">Cyan</option>
                  <option value="magenta">Magenta</option>
                  <option value="lime">Lime</option>
                  <option value="orange">Orange</option>
                </select>
              </div>
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.25rem',
              maxHeight: '150px',
              overflowY: 'auto'
            }}>
              {particleTypes.length > 0 ? (
                particleTypes.map(particleType => (
                  <label 
                    key={particleType}
                    style={{ 
                      fontWeight: 'normal',
                      fontSize: '0.9rem',
                      display: 'flex',
                      alignItems: 'center',
                      cursor: 'pointer'
                    }}
                  >
                    <input 
                      type="checkbox" 
                      checked={particles.includes(particleType)}
                      onChange={() => handleParticleToggle(particleType)}
                      style={{ width: 'auto', marginRight: '0.5rem' }}
                    />
                    {particleType}
                  </label>
                ))
              ) : (
                <div style={{ fontSize: '0.85rem', color: '#888', fontStyle: 'italic' }}>
                  No particle types available
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="control-group">
        <label>Annotations:</label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <label style={{ fontWeight: 'normal' }}>
            <input type="checkbox" checked={grids} onChange={(e) => setGrids(e.target.checked)} style={{ width: 'auto', marginRight: '0.5rem' }} />
            Grids
          </label>
          <label style={{ fontWeight: 'normal' }}>
            <input type="checkbox" checked={timestamp} onChange={(e) => setTimestamp(e.target.checked)} style={{ width: 'auto', marginRight: '0.5rem' }} />
            Timestamp
          </label>
        </div>
      </div>

      <div className="control-group">
        <label>Text Annotations:</label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <input type="text" value={topLeftText} onChange={(e) => setTopLeftText(e.target.value)} placeholder="Top Left Text" />
          <input type="text" value={topRightText} onChange={(e) => setTopRightText(e.target.value)} placeholder="Top Right Text" />
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

      <div className="control-group">
        <label>Export:</label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <button 
            onClick={onExportCurrentFrame} 
            disabled={isExporting}
            style={{ width: '100%' }}
          >
            Export Current Frame (PNG)
          </button>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <label style={{ fontWeight: 'normal', fontSize: '0.9rem', minWidth: '60px' }}>FPS:</label>
              <select 
                value={exportFps} 
                onChange={(e) => setExportFps(Number(e.target.value))}
                style={{ flex: 1 }}
              >
                {[1, 3, 5, 10, 15, 30].map(val => (
                  <option key={val} value={val}>{val}</option>
                ))}
              </select>
            </div>
            <button 
              onClick={onExportAnimation} 
              disabled={isExporting}
              style={{ width: '100%' }}
            >
              Export Animation (ZIP)
            </button>
          </div>

          {exportProgress && (
            <div style={{ 
              fontSize: '0.85rem', 
              color: isExporting ? '#4CAF50' : '#888',
              fontStyle: 'italic',
              textAlign: 'center',
              padding: '0.25rem'
            }}>
              {exportProgress}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Controls;
