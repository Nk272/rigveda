import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import * as d3 from 'd3';
import './BubbleVisualization.css';
import { useEntityStore } from '../store/entityStore';
import { fetchEntityRelationships } from '../services/api';

const BubbleVisualization = ({ entities }) => {
  const svgRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  
  const {
    selectedEntity,
    setSelectedEntity,
    hoveredEntity,
    setHoveredEntity,
    relationships,
    setRelationships,
    selectedRelationship,
    setSelectedRelationship,
    reset
  } = useEntityStore();
  
  useEffect(() => {
    const UpdateDimensions = () => {
      if (svgRef.current) {
        const container = svgRef.current.parentElement;
        setDimensions({
          width: container.clientWidth,
          height: container.clientHeight
        });
      }
    };
    
    UpdateDimensions();
    window.addEventListener('resize', UpdateDimensions);
    
    return () => window.removeEventListener('resize', UpdateDimensions);
  }, []);
  
  useEffect(() => {
    if (!entities.length || !dimensions.width) return;
    
    RenderBubbles();
  }, [entities, dimensions, selectedEntity, relationships]);
  
  const GetEntityColor = (entityType) => {
    const colors = {
      deity: '#FFD700',
      attribute: '#32CD32',
      rishi: '#4169E1',
    };
    return colors[entityType] || '#999999';
  };
  
  const GetBubbleRadius = (frequency) => {
    const minRadius = 15;
    const maxRadius = 50;
    const maxFreq = Math.max(...entities.map(e => e.frequency));
    const normalized = frequency / maxFreq;
    return minRadius + (normalized * (maxRadius - minRadius));
  };
  
  const HandleEntityClick = async (entity) => {
    if (selectedEntity && selectedEntity.id === entity.id) {
      reset();
      return;
    }
    
    setSelectedEntity(entity);
    
    try {
      const rels = await fetchEntityRelationships(entity.id);
      setRelationships(rels);
    } catch (error) {
      console.error('Error loading relationships:', error);
    }
  };
  
  const HandleRelatedEntityClick = (relatedEntity) => {
    const relationship = relationships.find(
      r => r.relatedEntityId === relatedEntity.id
    );
    
    if (relationship) {
      setSelectedRelationship(relationship);
    }
  };
  
  const RenderBubbles = () => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    
    const { width, height } = dimensions;
    const centerX = width / 2;
    const centerY = height / 2;
    
    const g = svg.append('g');
    
    if (!selectedEntity) {
      const simulation = d3.forceSimulation(entities)
        .force('charge', d3.forceManyBody().strength(-100))
        .force('center', d3.forceCenter(centerX, centerY))
        .force('collision', d3.forceCollide().radius(d => GetBubbleRadius(d.frequency) + 5))
        .alphaDecay(0.02);
      
      const bubbles = g.selectAll('circle')
        .data(entities)
        .enter()
        .append('circle')
        .attr('r', d => GetBubbleRadius(d.frequency))
        .attr('fill', d => GetEntityColor(d.entityType))
        .attr('opacity', 0.7)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('click', (event, d) => HandleEntityClick(d))
        .on('mouseenter', (event, d) => setHoveredEntity(d))
        .on('mouseleave', () => setHoveredEntity(null));
      
      const labels = g.selectAll('text')
        .data(entities)
        .enter()
        .append('text')
        .text(d => d.name)
        .attr('text-anchor', 'middle')
        .attr('dy', 4)
        .attr('font-size', d => Math.max(10, GetBubbleRadius(d.frequency) / 3))
        .attr('fill', '#000')
        .attr('pointer-events', 'none')
        .attr('font-weight', 'bold');
      
      simulation.on('tick', () => {
        bubbles
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
        
        labels
          .attr('x', d => d.x)
          .attr('y', d => d.y);
      });
    } else {
      const mainBubble = g.append('circle')
        .attr('cx', centerX)
        .attr('cy', centerY)
        .attr('r', GetBubbleRadius(selectedEntity.frequency) * 1.5)
        .attr('fill', GetEntityColor(selectedEntity.entityType))
        .attr('opacity', 0.9)
        .attr('stroke', '#fff')
        .attr('stroke-width', 3)
        .style('cursor', 'pointer')
        .on('click', () => reset());
      
      g.append('text')
        .attr('x', centerX)
        .attr('y', centerY)
        .attr('text-anchor', 'middle')
        .attr('dy', 5)
        .attr('font-size', 20)
        .attr('fill', '#000')
        .attr('font-weight', 'bold')
        .text(selectedEntity.name);
      
      if (relationships.length > 0) {
        const angleStep = (2 * Math.PI) / relationships.length;
        const radius = Math.min(width, height) / 3;
        
        relationships.forEach((rel, i) => {
          const angle = i * angleStep;
          const x = centerX + radius * Math.cos(angle);
          const y = centerY + radius * Math.sin(angle);
          
          const lineOpacity = selectedRelationship && 
            selectedRelationship.relatedEntityId === rel.relatedEntityId ? 1 : 0.3;
          
          g.append('line')
            .attr('x1', centerX)
            .attr('y1', centerY)
            .attr('x2', x)
            .attr('y2', y)
            .attr('stroke', '#999')
            .attr('stroke-width', rel.score * 5)
            .attr('opacity', lineOpacity);
          
          const relatedRadius = GetBubbleRadius(rel.score * 100);
          
          const isSelected = selectedRelationship && 
            selectedRelationship.relatedEntityId === rel.relatedEntityId;
          
          g.append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', isSelected ? relatedRadius * 1.3 : relatedRadius)
            .attr('fill', GetEntityColor(rel.relatedEntityType))
            .attr('opacity', isSelected ? 1 : 0.7)
            .attr('stroke', isSelected ? '#000' : '#fff')
            .attr('stroke-width', isSelected ? 3 : 2)
            .style('cursor', 'pointer')
            .on('click', () => HandleRelatedEntityClick({ id: rel.relatedEntityId }));
          
          g.append('text')
            .attr('x', x)
            .attr('y', y)
            .attr('text-anchor', 'middle')
            .attr('dy', 4)
            .attr('font-size', Math.max(10, relatedRadius / 2))
            .attr('fill', '#000')
            .attr('font-weight', isSelected ? 'bold' : 'normal')
            .attr('pointer-events', 'none')
            .text(rel.relatedEntityName);
        });
      }
    }
  };
  
  return (
    <div className="bubble-visualization">
      <div className="dotted-background"></div>
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="bubble-svg"
      />
      
      {hoveredEntity && !selectedEntity && (
        <motion.div
          className="hover-tooltip"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <h3>{hoveredEntity.name}</h3>
          <p>Type: {hoveredEntity.entityType}</p>
          <p>Frequency: {hoveredEntity.frequency}</p>
        </motion.div>
      )}
    </div>
  );
};

export default BubbleVisualization;
