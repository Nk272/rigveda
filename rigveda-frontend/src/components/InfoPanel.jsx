import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './InfoPanel.css';
import { useEntityStore } from '../store/entityStore';

const InfoPanel = () => {
  const { 
    selectedEntity, 
    selectedRelationship, 
    relationships,
    reset 
  } = useEntityStore();
  
  if (!selectedEntity) return null;
  
  return (
    <AnimatePresence>
      <motion.div
        className="info-panel"
        initial={{ x: 400 }}
        animate={{ x: 0 }}
        exit={{ x: 400 }}
        transition={{ type: 'spring', damping: 20 }}
      >
        <div className="panel-header">
          <h2>{selectedEntity.name}</h2>
          <button className="close-button" onClick={reset}>✕</button>
        </div>
        
        <div className="panel-content">
          <div className="entity-info">
            <div className="info-item">
              <span className="label">Type:</span>
              <span className="value">{selectedEntity.entityType}</span>
            </div>
            <div className="info-item">
              <span className="label">Frequency:</span>
              <span className="value">{selectedEntity.frequency}</span>
            </div>
          </div>
          
          {!selectedRelationship && relationships.length > 0 && (
            <div className="relationships-section">
              <h3>Relationships ({relationships.length})</h3>
              <div className="relationships-list">
                {relationships.slice(0, 10).map((rel, idx) => (
                  <div key={idx} className="relationship-item">
                    <div className="rel-name">{rel.relatedEntityName}</div>
                    <div className="rel-score">
                      <div 
                        className="score-bar" 
                        style={{ width: `${rel.score * 100}%` }}
                      ></div>
                      <span>{(rel.score * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {selectedRelationship && (
            <div className="relationship-detail">
              <button 
                className="back-button"
                onClick={() => useEntityStore.getState().setSelectedRelationship(null)}
              >
                ← Back to relationships
              </button>
              
              <h3>Relationship with {selectedRelationship.relatedEntityName}</h3>
              
              <div className="score-breakdown">
                <div className="score-item">
                  <span className="score-label">Overall Score:</span>
                  <span className="score-value">
                    {(selectedRelationship.score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="score-item">
                  <span className="score-label">Conjunction:</span>
                  <span className="score-value">
                    {(selectedRelationship.conjunctionScore * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="score-item">
                  <span className="score-label">Hymn Co-occurrence:</span>
                  <span className="score-value">
                    {(selectedRelationship.hymnCooccurrenceScore * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="score-item">
                  <span className="score-label">Indirect:</span>
                  <span className="score-value">
                    {(selectedRelationship.indirectScore * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
              
              {selectedRelationship.hymnReferences && 
               selectedRelationship.hymnReferences.length > 0 && (
                <div className="hymn-references">
                  <h4>Hymn References</h4>
                  <ul>
                    {selectedRelationship.hymnReferences.map((ref, idx) => (
                      <li key={idx}>{ref}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {selectedRelationship.conjunctionContexts && 
               selectedRelationship.conjunctionContexts.length > 0 && (
                <div className="conjunction-contexts">
                  <h4>Conjunction Examples</h4>
                  <ul>
                    {selectedRelationship.conjunctionContexts.map((context, idx) => (
                      <li key={idx}>"{context}"</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default InfoPanel;
