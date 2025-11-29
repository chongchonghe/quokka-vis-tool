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
  fieldUnit, setFieldUnit,
  particles, setParticles,
  particleTypes,
  particleSize, setParticleSize,
  particleColor, setParticleColor,
  grids, setGrids,
  timestamp, setTimestamp,
  topLeftText, setTopLeftText,
  topRightText, setTopRightText,
  // 3D props
  cameraX, setCameraX,
  cameraY, setCameraY,
  cameraZ, setCameraZ,
  nLayers, setNLayers,
  alphaMin, setAlphaMin,
  alphaMax, setAlphaMax,
  greyOpacity, setGreyOpacity,
  previewMode, setPreviewMode,
  showBoxFrame, setShowBoxFrame,
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
        <div className="animation-controls">
          <button onClick={() => setIsPlaying(!isPlaying)}>
            {isPlaying ? 'Pause Animation' : 'Play Animation'}
          </button>

          <div className="fps-buttons">
            {[0.3, 0.5, 1, 2, 3, 5].map(val => (
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
          <option value="vol">Volume Rendering</option>
        </select>
      </div>

      {plotType === 'vol' && (
        <div className="control-group">
          <label style={{marginBottom: '0.5rem', display: 'block', fontWeight: 'bold', fontSize: '0.9rem'}}>3D Camera Direction:</label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{fontSize: '0.8rem', display: 'block'}}>X</label>
              <input type="number" value={cameraX} onChange={(e) => setCameraX(Number(e.target.value))} step="0.1" style={{width: '100%'}} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{fontSize: '0.8rem', display: 'block'}}>Y</label>
              <input type="number" value={cameraY} onChange={(e) => setCameraY(Number(e.target.value))} step="0.1" style={{width: '100%'}} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{fontSize: '0.8rem', display: 'block'}}>Z</label>
              <input type="number" value={cameraZ} onChange={(e) => setCameraZ(Number(e.target.value))} step="0.1" style={{width: '100%'}} />
            </div>
          </div>
          
          <label style={{marginTop: '0.5rem', marginBottom: '0.5rem', display: 'block', fontWeight: 'bold', fontSize: '0.9rem'}}>Transfer Function:</label>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{fontSize: '0.8rem', display: 'block'}}>Layers</label>
              <input type="number" value={nLayers} onChange={(e) => setNLayers(Number(e.target.value))} min="1" max="20" style={{width: '100%'}} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{fontSize: '0.8rem', display: 'block'}}>Min Alpha</label>
              <input type="number" value={alphaMin} onChange={(e) => setAlphaMin(Number(e.target.value))} step="0.1" min="0" max="1" style={{width: '100%'}} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{fontSize: '0.8rem', display: 'block'}}>Max Alpha</label>
              <input type="number" value={alphaMax} onChange={(e) => setAlphaMax(Number(e.target.value))} step="0.1" min="0" max="1" style={{width: '100%'}} />
            </div>
          </div>
          
          <div style={{ marginTop: '0.5rem' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem', display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={greyOpacity} 
                onChange={(e) => setGreyOpacity(e.target.checked)} 
                style={{ width: 'auto', marginRight: '0.5rem' }} 
              />
              Grey Opacity (Opaque Channels)
            </label>
          </div>
          
          <div style={{ marginTop: '0.5rem' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem', display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={previewMode} 
                onChange={(e) => setPreviewMode(e.target.checked)} 
                style={{ width: 'auto', marginRight: '0.5rem' }} 
              />
              Preview Mode (Low Res)
            </label>
          </div>
          
          <div style={{ marginTop: '0.5rem' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem', display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={showBoxFrame} 
                onChange={(e) => setShowBoxFrame(e.target.checked)} 
                style={{ width: 'auto', marginRight: '0.5rem' }} 
              />
              Show Box Frame
            </label>
          </div>
        </div>
      )}

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
        <label>Field Unit:</label>
        <input 
          type="text" 
          value={fieldUnit} 
          onChange={(e) => setFieldUnit(e.target.value)} 
          placeholder="e.g. Msun/pc**3"
          style={{ flex: 1 }}
        />
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
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem', whiteSpace: 'nowrap' }}>Min:</label>
            <input type="number" value={vmin} onChange={(e) => setVmin(e.target.value)} placeholder="Auto" />
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem', whiteSpace: 'nowrap' }}>Max:</label>
            <input type="number" value={vmax} onChange={(e) => setVmax(e.target.value)} placeholder="Auto" />
          </div>
        </div>
      </div>

      <div className="control-group compact">
        <label>Width:</label>
        <input type="number" value={widthValue} onChange={(e) => setWidthValue(e.target.value)} placeholder="Full" style={{ flex: 1 }} />
        <input type="text" value={widthUnit} onChange={(e) => setWidthUnit(e.target.value)} placeholder="Unit (e.g. kpc)" style={{ flex: 1 }} />
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

      <div className="control-group compact">
        <label>Annotations:</label>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <label style={{ fontWeight: 'normal', fontSize: '0.9rem', display: 'flex', alignItems: 'center', whiteSpace: 'nowrap' }}>
            <input type="checkbox" checked={grids} onChange={(e) => setGrids(e.target.checked)} style={{ width: 'auto', marginRight: '0.3rem' }} />
            Grids
          </label>
          <label style={{ fontWeight: 'normal', fontSize: '0.9rem', display: 'flex', alignItems: 'center', whiteSpace: 'nowrap' }}>
            <input type="checkbox" checked={timestamp} onChange={(e) => setTimestamp(e.target.checked)} style={{ width: 'auto', marginRight: '0.3rem' }} />
            Timestamp
          </label>
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem' }}>Label:</label>
            <input 
              type="text" 
              value={colorbarLabel} 
              onChange={(e) => setColorbarLabel(e.target.value)} 
              placeholder="Default"
              style={{ flexGrow: 1 }}
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
          <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem', whiteSpace: 'nowrap' }}>
              Custom Size:
            </label>
            <input 
              type="text" 
              value={scaleBarSize} 
              onChange={(e) => setScaleBarSize(e.target.value)} 
              placeholder="Auto"
              style={{ flexGrow: 1 }}
            />
            <input 
              type="text" 
              value={scaleBarUnit} 
              onChange={(e) => setScaleBarUnit(e.target.value)} 
              placeholder="Unit"
              style={{ flexGrow: 1 }}
            />
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

      <div className="control-group" style={{ marginTop: '0.5rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input type="text" value={topLeftText} onChange={(e) => setTopLeftText(e.target.value)} placeholder="Top Left Text" />
          <input type="text" value={topRightText} onChange={(e) => setTopRightText(e.target.value)} placeholder="Top Right Text" />
        </div>
      </div>

      <div className="control-group">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <button 
            onClick={onExportCurrentFrame} 
            disabled={isExporting}
            style={{ width: '100%' }}
          >
            Export Current Frame (PNG)
          </button>
          
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <label style={{ fontWeight: 'normal', fontSize: '0.9rem', whiteSpace: 'nowrap' }}>FPS:</label>
            <select 
              value={exportFps} 
              onChange={(e) => setExportFps(Number(e.target.value))}
              style={{ width: '60px' }}
            >
              {[1, 3, 5, 10, 15, 30].map(val => (
                <option key={val} value={val}>{val}</option>
              ))}
            </select>
            <button 
              onClick={onExportAnimation} 
              disabled={isExporting}
              style={{ flex: 1 }}
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
