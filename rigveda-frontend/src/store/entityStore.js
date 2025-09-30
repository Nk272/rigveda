import { create } from 'zustand';

export const useEntityStore = create((set) => ({
  entities: [],
  selectedEntity: null,
  hoveredEntity: null,
  relationships: [],
  selectedRelationship: null,
  loading: false,
  error: null,
  
  setEntities: (entities) => set({ entities }),
  
  setSelectedEntity: (entity) => set({ 
    selectedEntity: entity,
    selectedRelationship: null 
  }),
  
  setHoveredEntity: (entity) => set({ hoveredEntity: entity }),
  
  setRelationships: (relationships) => set({ relationships }),
  
  setSelectedRelationship: (relationship) => set({ 
    selectedRelationship: relationship 
  }),
  
  setLoading: (loading) => set({ loading }),
  
  setError: (error) => set({ error }),
  
  reset: () => set({
    selectedEntity: null,
    hoveredEntity: null,
    relationships: [],
    selectedRelationship: null,
  }),
}));
