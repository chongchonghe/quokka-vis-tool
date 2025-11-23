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
      const res = await fetch('http://localhost:8000/api/datasets');
      const data = await res.json();
      setDatasets(data.datasets);
      if (data.datasets.length > 0) {
        setCurrentDataset(data.datasets[0]);
      }
    } catch (err) {
      console.error("Failed to fetch datasets:", err);
    }
  };

  const loadDataset = async (filename) => {
    try {
      setCurrentDataset(filename);
      const res = await fetch(`http://localhost:8000/api/load_dataset?filename=${filename}`, { method: 'POST' });
      const data = await res.json();
      setDatasetInfo(data);
      
      const fieldsRes = await fetch('http://localhost:8000/api/fields');
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
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="sidebar-header">
          <h1>AMReX Viz Tool</h1>
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
        />
      </div>
      <div className="main-content">
        <Viewer 
          axis={axis} 
          field={field} 
          coord={coord} 
          refreshTrigger={refreshTrigger}
        />
      </div>
    </div>
  )
}

export default App
