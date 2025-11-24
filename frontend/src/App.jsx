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
    fetchDatasets();
  }, []);

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
      const res = await fetch('/api/datasets');
      const data = await res.json();
      setDatasets(data.datasets);
      // Don't set currentDataset here, let the useEffect handle it to trigger loadDataset
    } catch (err) {
      console.error("Failed to fetch datasets:", err);
    }
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
          {datasetInfo && <span className="dataset-info">Dataset: {datasetInfo.message}</span>}
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
