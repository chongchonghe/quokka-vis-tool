import { useState, useEffect } from 'react'
import './App.css'
import Viewer from './components/Viewer'
import Controls from './components/Controls'

function App() {
  const [axis, setAxis] = useState('z');
  const [field, setField] = useState('density');
  const [coord, setCoord] = useState(null);
  const [fieldsList, setFieldsList] = useState([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [datasetInfo, setDatasetInfo] = useState(null);

  useEffect(() => {
    // Load dataset and fields on mount
    loadDataset();
  }, []);

  const loadDataset = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/load_dataset', { method: 'POST' });
      const data = await res.json();
      setDatasetInfo(data);
      
      const fieldsRes = await fetch('http://localhost:8000/api/fields');
      const fieldsData = await fieldsRes.json();
      setFieldsList(fieldsData.fields);
      if (fieldsData.fields.length > 0) {
        setField(fieldsData.fields[0]);
      }
    } catch (err) {
      console.error("Failed to init:", err);
    }
  };

  const handleRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="app-container">
      <header>
        <h1>AMReX Viz Tool</h1>
        {datasetInfo && <span className="dataset-info">Dataset: {datasetInfo.message}</span>}
      </header>
      
      <main>
        <div className="sidebar">
          <Controls 
            axis={axis} setAxis={setAxis}
            field={field} setField={setField}
            fieldsList={fieldsList}
            coord={coord} setCoord={setCoord}
            onRefresh={handleRefresh}
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
      </main>
    </div>
  )
}

export default App
