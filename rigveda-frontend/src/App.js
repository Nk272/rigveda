import React, { useEffect, useState } from 'react';
import './App.css';
import BubbleVisualization from './components/BubbleVisualization';
import InfoPanel from './components/InfoPanel';
import { useEntityStore } from './store/entityStore';
import { fetchEntities } from './services/api';

function App() {
  const { entities, setEntities, loading, setLoading, error, setError } = useEntityStore();
  
  useEffect(() => {
    LoadEntities();
  }, []);
  
  const LoadEntities = async () => {
    try {
      setLoading(true);
      const data = await fetchEntities();
      setEntities(data);
      setError(null);
    } catch (err) {
      setError('Failed to load entities');
      console.error('Error loading entities:', err);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading Rigveda entities...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="error-container">
        <p>{error}</p>
        <button onClick={LoadEntities}>Retry</button>
      </div>
    );
  }
  
  return (
    <div className="App">
      <header className="app-header">
        <h1>Rigveda Word Relationships</h1>
        <p>Explore connections between entities in the Rigveda</p>
      </header>
      
      <div className="app-container">
        <BubbleVisualization entities={entities} />
        <InfoPanel />
      </div>
    </div>
  );
}

export default App;
