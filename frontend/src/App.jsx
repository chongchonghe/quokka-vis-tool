import { useState, useEffect } from 'react'
import './App.css'
import Viewer from './components/Viewer'
import Controls from './components/Controls'

function App() {
  const [axis, setAxis] = useState('z');
  const [field, setField] = useState(null);
  const [coord, setCoord] = useState(null);
  const [fieldsList, setFieldsList] = useState([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [datasetInfo, setDatasetInfo] = useState(null);
  
  const [dataDir, setDataDir] = useState('');
  const [serverInfo, setServerInfo] = useState(null);
  
  const [datasetPrefix, setDatasetPrefix] = useState('plt');
  
  // Animation state
  const [datasets, setDatasets] = useState([]);
  const [currentDataset, setCurrentDataset] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [fps, setFps] = useState(1);
  const [showColorbar, setShowColorbar] = useState(false);
  const [vmin, setVmin] = useState('');
  const [vmax, setVmax] = useState('');
  const [appliedVmin, setAppliedVmin] = useState('');
  const [appliedVmax, setAppliedVmax] = useState('');
  const [logScale, setLogScale] = useState(true);
  const [colorbarLabel, setColorbarLabel] = useState('');
  const [appliedColorbarLabel, setAppliedColorbarLabel] = useState('');
  const [colorbarOrientation, setColorbarOrientation] = useState('right');
  const [appliedColorbarOrientation, setAppliedColorbarOrientation] = useState('right');
  const [cmap, setCmap] = useState('viridis');
  const [dpi, setDpi] = useState(300);
  const [showScaleBar, setShowScaleBar] = useState(false);
  const [scaleBarSize, setScaleBarSize] = useState('');
  const [scaleBarUnit, setScaleBarUnit] = useState('');
  const [appliedScaleBarSize, setAppliedScaleBarSize] = useState('');
  const [appliedScaleBarUnit, setAppliedScaleBarUnit] = useState('');
  const [appliedDpi, setAppliedDpi] = useState(300);

  useEffect(() => {
    // Load initial data
    fetchServerInfo();
    fetchDatasets();
  }, []);

  const fetchServerInfo = async () => {
    console.log("Fetching server info...");
    try {
      const res = await fetch('/api/server_info');
      console.log("Server info response status:", res.status);
      const data = await res.json();
      console.log("Server info data:", data);
      setServerInfo(data);
    } catch (err) {
      console.error("Failed to fetch server info:", err);
    }
  };

  const testPath = async (pathToTest) => {
    console.log("========================================");
    console.log("Testing path:", pathToTest);
    console.log("Encoded path:", encodeURIComponent(pathToTest));
    
    try {
      const url = `/api/test_path?path=${encodeURIComponent(pathToTest)}`;
      console.log("Full URL:", window.location.origin + url);
      console.log("Fetching...");
      
      const res = await fetch(url);
      console.log("Response status:", res.status);
      console.log("Response ok:", res.ok);
      
      if (!res.ok) {
        const text = await res.text();
        console.error("Error response:", text);
        return {
          error: true,
          status: res.status,
          message: text
        };
      }
      
      const data = await res.json();
      console.log("Path test results:", data);
      console.log("========================================");
      return data;
    } catch (err) {
      console.error("========================================");
      console.error("Failed to test path - Exception caught");
      console.error("Error type:", err.constructor.name);
      console.error("Error message:", err.message);
      console.error("Error stack:", err.stack);
      console.error("========================================");
      
      return {
        error: true,
        message: err.message,
        type: err.constructor.name
      };
    }
  };

  useEffect(() => {
    if (datasets.length > 0 && !currentDataset) {
      loadDataset(datasets[0]);
    }
  }, [datasets]);

  // Animation loop
  useEffect(() => {
    let interval;
    if (isPlaying && datasets.length > 0) {
      interval = setInterval(() => {
        const currentIndex = datasets.indexOf(currentDataset);
        const nextIndex = (currentIndex + 1) % datasets.length;
        loadDataset(datasets[nextIndex]);
      }, 1000 / fps);
    }
    return () => clearInterval(interval);
  }, [isPlaying, datasets, currentDataset, fps]);

  const fetchDatasets = async () => {
    try {
      const res = await fetch(`/api/datasets?prefix=${datasetPrefix}`);
      const data = await res.json();
      setDatasets(data.datasets);
      // Don't set currentDataset here, let the useEffect handle it to trigger loadDataset
    } catch (err) {
      console.error("Failed to fetch datasets:", err);
    }
  };

  const handleSetDataDir = async () => {
    console.log("========================================");
    console.log("handleSetDataDir called");
    console.log("dataDir value:", dataDir);
    console.log("dataDir type:", typeof dataDir);
    console.log("dataDir length:", dataDir.length);
    
    if (!dataDir) {
      console.error("dataDir is empty, returning");
      alert("Please enter a data directory path");
      return;
    }
    
    const requestBody = { path: dataDir };
    console.log("Request body:", requestBody);
    console.log("Request body JSON:", JSON.stringify(requestBody));
    
    try {
      console.log("Sending POST request to /api/set_data_dir");
      console.log("Full URL:", window.location.origin + '/api/set_data_dir');
      
      const res = await fetch('/api/set_data_dir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      console.log("Response received");
      console.log("Response status:", res.status);
      console.log("Response ok:", res.ok);
      console.log("Response headers:", Object.fromEntries(res.headers.entries()));
      
      if (res.ok) {
        const data = await res.json();
        console.log("Success response data:", data);
        alert(`Data directory set to: ${data.path}`);
        fetchDatasets();
      } else {
        console.error("Error response");
        const contentType = res.headers.get("content-type");
        console.log("Content-Type:", contentType);
        
        if (contentType && contentType.includes("application/json")) {
          const err = await res.json();
          console.error("Error details:", err);
          console.error("Error detail message:", err.detail);
          alert(`Error: ${err.detail}\n\nNote: Path must exist on the SERVER where the backend is running, not your local machine.`);
        } else {
          const text = await res.text();
          console.error("Non-JSON error response:", text);
          alert(`Error (${res.status}): ${text}\n\nNote: Path must exist on the SERVER where the backend is running, not your local machine.`);
        }
      }
    } catch (err) {
      console.error("========================================");
      console.error("Exception caught in handleSetDataDir");
      console.error("Error type:", err.constructor.name);
      console.error("Error message:", err.message);
      console.error("Error stack:", err.stack);
      console.error("========================================");
      alert(`Failed to set data directory: ${err.message}\n\nThe path must exist on the server where the backend is running.`);
    }
    
    console.log("handleSetDataDir complete");
    console.log("========================================\n");
  };

  const loadDataset = async (filename) => {
    try {
      setCurrentDataset(filename);
      const res = await fetch(`/api/load_dataset?filename=${filename}`, { method: 'POST' });
      const data = await res.json();
      setDatasetInfo(data);
      
      const fieldsRes = await fetch('/api/fields');
      const fieldsData = await fieldsRes.json();
      setFieldsList(fieldsData.fields);
      
      // Keep current field if available, else default to first
      if (fieldsData.fields.length > 0) {
        if (!field || !fieldsData.fields.includes(field)) {
          setField(fieldsData.fields[0]);
        }
      }
      
      // Trigger refresh of viewer
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      console.error("Failed to load dataset:", err);
    }
  };

  const handleRefresh = () => {
    setAppliedVmin(vmin);
    setAppliedVmax(vmax);
    setAppliedColorbarLabel(colorbarLabel);
    setAppliedColorbarOrientation(colorbarOrientation);
    setAppliedScaleBarSize(scaleBarSize);
    setAppliedScaleBarUnit(scaleBarUnit);
    setAppliedDpi(dpi);
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="sidebar-header">
          <h1>QUOKKA Viz Tool</h1>
          {serverInfo && (
            <div style={{ fontSize: '0.85rem', color: '#888', marginBottom: '0.5rem' }}>
              Backend: <strong>{serverInfo.hostname}</strong>
              <br />
              Data Dir: {serverInfo.current_data_directory}
            </div>
          )}
          <div style={{ marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input 
                type="text" 
                value={dataDir} 
                onChange={(e) => setDataDir(e.target.value)} 
                placeholder={serverInfo ? "/path/on/" + serverInfo.hostname : "/path/to/data"}
                style={{ flex: 1, padding: '0.25rem' }}
              />
              <button onClick={handleSetDataDir} style={{ padding: '0.25rem 0.5rem' }}>Set</button>
              <button 
                onClick={() => {
                  if (!dataDir) {
                    alert("Please enter a path first");
                    return;
                  }
                  testPath(dataDir).then(result => {
                    if (!result) {
                      alert("Test returned null - check browser console for details");
                    } else if (result.error) {
                      alert(`Test Error:\n\n${result.message}\n\nCheck browser console for more details`);
                    } else {
                      const summary = `Path Test Results:

Server: ${result.server_hostname}
Path: ${result.path}
Exists: ${result.exists ? 'YES ✓' : 'NO ✗'}
Is Directory: ${result.is_dir ? 'YES ✓' : 'NO ✗'}
Can Read: ${result.can_read ? 'YES ✓' : 'NO ✗'}
${result.contents_count ? '\nItems in directory: ' + result.contents_count : ''}

Full details in browser console (F12)`;
                      alert(summary);
                    }
                  });
                }} 
                style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                title="Test if path exists on server"
              >
                Test
              </button>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <label style={{ fontSize: '0.9rem' }}>Prefix:</label>
              <input 
                type="text" 
                value={datasetPrefix} 
                onChange={(e) => setDatasetPrefix(e.target.value)} 
                style={{ flex: 1, padding: '0.25rem' }}
              />
              <button onClick={fetchDatasets} style={{ padding: '0.25rem 0.5rem' }}>Filter</button>
            </div>
          </div>
          {datasetInfo && <span className="dataset-info">Loaded: {currentDataset}</span>}
        </div>
        <Controls 
          axis={axis} setAxis={setAxis}
          field={field} setField={setField}
          fieldsList={fieldsList}
          coord={coord} setCoord={setCoord}
          onRefresh={handleRefresh}
          datasets={datasets}
          currentDataset={currentDataset}
          setDataset={loadDataset}
          isPlaying={isPlaying}
          setIsPlaying={setIsPlaying}
          fps={fps}
          setFps={setFps}
          showColorbar={showColorbar}
          setShowColorbar={setShowColorbar}
          vmin={vmin}
          setVmin={setVmin}
          vmax={vmax}
          setVmax={setVmax}
          logScale={logScale}
          setLogScale={setLogScale}
          colorbarLabel={colorbarLabel}
          setColorbarLabel={setColorbarLabel}
          colorbarOrientation={colorbarOrientation}
          setColorbarOrientation={setColorbarOrientation}
          cmap={cmap}
          setCmap={setCmap}
          dpi={dpi}
          setDpi={setDpi}
          showScaleBar={showScaleBar}
          setShowScaleBar={setShowScaleBar}
          scaleBarSize={scaleBarSize}
          setScaleBarSize={setScaleBarSize}
          scaleBarUnit={scaleBarUnit}
          setScaleBarUnit={setScaleBarUnit}
        />
      </div>
      <div className="main-content">
        <Viewer 
          axis={axis} 
          field={field} 
          coord={coord} 
          refreshTrigger={refreshTrigger}
          showColorbar={showColorbar}
          vmin={appliedVmin}
          vmax={appliedVmax}
          logScale={logScale}
          colorbarLabel={appliedColorbarLabel}
          colorbarOrientation={appliedColorbarOrientation}
          cmap={cmap}
          showScaleBar={showScaleBar}
          scaleBarSize={appliedScaleBarSize}
          scaleBarUnit={appliedScaleBarUnit}
          dpi={appliedDpi}
        />
      </div>
    </div>
  )
}

export default App
