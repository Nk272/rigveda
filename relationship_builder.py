import json
import re
from collections import defaultdict, Counter
from itertools import combinations
import math
import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer

class RelationshipMatrixBuilder:
    def __init__(self, data_file="rigveda_data.json"):
        print("Loading Rigveda data...")
        with open(data_file, "r", encoding='utf-8') as file:
            self.data = json.load(file)
        
        self.entities = {}
        self.relationships = defaultdict(lambda: {
            'conjunction_score': 0.0,
            'hymn_cooccurrence_score': 0.0,
            'indirect_score': 0.0,
            'final_score': 0.0,
            'hymn_references': [],
            'conjunction_contexts': []
        })
        
        self.entityHymnIndex = defaultdict(set)
        self.entityCooccurrence = defaultdict(lambda: defaultdict(int))
        self.conjunctionPatterns = [
            r'\b(\w+)\s+and\s+(\w+)\b',
            r'\b(\w+)\s+with\s+(\w+)\b',
            r'\b(\w+)\s+or\s+(\w+)\b',
            r'\b(\w+),\s+(\w+)\b'
        ]
        
        self.lemmatizer = WordNetLemmatizer()
        self.attributeClusters = defaultdict(set)
        
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
            nltk.download('omw-1.4')
    
    def CleanWord(self, word):
        """Clean and normalize words"""
        word = word.lower().strip().strip(".,!?\"'():-_")
        return word if len(word) > 1 else None
    
    def GetSemanticSimilarity(self, word1, word2):
        """Calculate semantic similarity using WordNet"""
        synsets1 = wordnet.synsets(word1)
        synsets2 = wordnet.synsets(word2)
        
        if not synsets1 or not synsets2:
            return 0.0
        
        maxSimilarity = 0.0
        for syn1 in synsets1:
            for syn2 in synsets2:
                try:
                    similarity = syn1.path_similarity(syn2)
                    if similarity is not None:
                        maxSimilarity = max(maxSimilarity, similarity)
                except:
                    continue
        
        return maxSimilarity
    
    def ExtractNamedEntities(self):
        """Extract deities and important named entities from hymns"""
        print("\n=== Phase 1: Extracting Named Entities ===")
        
        deityNames = Counter()
        wordFrequencies = Counter()
        
        for bookNum, book in self.data['books'].items():
            for hymnNum, hymn in book['hymns'].items():
                title = hymn.get('title', '')
                text = hymn.get('text', '')
                
                titleParts = title.split('.')
                if len(titleParts) >= 2:
                    deityName = titleParts[-1].strip()
                    if deityName:
                        deityNames[deityName] += 1
                
                words = text.split()
                for word in words:
                    cleaned = self.CleanWord(word)
                    if cleaned and len(cleaned) > 2:
                        wordFrequencies[cleaned] += 1
        
        print(f"Found {len(deityNames)} unique deity names")
        
        stopwords = {'the', 'and', 'with', 'for', 'thou', 'thee', 'thy', 'our', 
                    'who', 'hath', 'from', 'have', 'this', 'that', 'they', 'their'}
        
        importantWords = {word: count for word, count in wordFrequencies.items() 
                         if count >= 20 and word not in stopwords and word.istitle()}
        
        print(f"Found {len(importantWords)} important named words (freq >= 20)")
        
        entityId = 1
        for deity, count in deityNames.most_common():
            self.entities[deity] = {
                'id': entityId,
                'name': deity,
                'type': 'deity',
                'frequency': count
            }
            entityId += 1
        
        for word, count in sorted(importantWords.items(), key=lambda x: x[1], reverse=True)[:150]:
            if word not in self.entities:
                self.entities[word] = {
                    'id': entityId,
                    'name': word,
                    'type': 'attribute',
                    'frequency': count
                }
                entityId += 1
        
        print(f"Total entities extracted: {len(self.entities)}")
        
        with open("entities.json", "w", encoding='utf-8') as f:
            json.dump(dict(sorted(self.entities.items(), 
                                 key=lambda x: x[1]['frequency'], reverse=True)), 
                     f, indent=2, ensure_ascii=False)
        
        return self.entities
    
    def ClusterSimilarAttributes(self):
        """Cluster semantically similar attribute words"""
        print("\n=== Phase 2: Clustering Similar Attributes ===")
        
        attributes = [name for name, entity in self.entities.items() 
                     if entity['type'] == 'attribute']
        
        processed = set()
        
        for i, attr1 in enumerate(attributes):
            if attr1 in processed:
                continue
            
            self.attributeClusters[attr1].add(attr1)
            
            for attr2 in attributes[i+1:]:
                if attr2 in processed:
                    continue
                
                similarity = self.GetSemanticSimilarity(attr1, attr2)
                
                if similarity >= 0.7:
                    self.attributeClusters[attr1].add(attr2)
                    processed.add(attr2)
                    
                    combinedFreq = self.entities[attr1]['frequency'] + self.entities[attr2]['frequency']
                    self.entities[attr1]['frequency'] = combinedFreq
        
        clustersFound = sum(1 for cluster in self.attributeClusters.values() if len(cluster) > 1)
        print(f"Created {clustersFound} attribute clusters")
        
        clusterDict = {main: list(cluster) for main, cluster in self.attributeClusters.items() 
                      if len(cluster) > 1}
        
        with open("attribute_clusters.json", "w", encoding='utf-8') as f:
            json.dump(clusterDict, f, indent=2, ensure_ascii=False)
        
        return self.attributeClusters
    
    def BuildEntityHymnIndex(self):
        """Build an index of which entities appear in which hymns"""
        print("\n=== Phase 3: Building Entity-Hymn Index ===")
        
        entityPatterns = {}
        for entityName in self.entities.keys():
            entityPatterns[entityName] = re.compile(
                r'\b' + re.escape(entityName.lower()) + r'\b', 
                re.IGNORECASE
            )
        
        for bookNum, book in self.data['books'].items():
            for hymnNum, hymn in book['hymns'].items():
                text = hymn.get('text', '')
                hymnRef = f"Book {book['book_number']}, Hymn {hymn['hymn_number']}"
                
                for entityName, pattern in entityPatterns.items():
                    if pattern.search(text):
                        self.entityHymnIndex[entityName].add(hymnRef)
        
        print(f"Indexed {sum(len(hymns) for hymns in self.entityHymnIndex.values())} entity-hymn occurrences")
    
    def CalculateConjunctionScore(self):
        """Calculate scores for entities appearing in conjunction"""
        print("\n=== Phase 4: Calculating Conjunction Scores ===")
        
        conjunctionPairs = defaultdict(list)
        
        for bookNum, book in self.data['books'].items():
            for hymnNum, hymn in book['hymns'].items():
                text = hymn.get('text', '')
                hymnRef = f"Book {book['book_number']}, Hymn {hymn['hymn_number']}"
                
                for pattern in self.conjunctionPatterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        word1 = self.CleanWord(match.group(1))
                        word2 = self.CleanWord(match.group(2))
                        
                        if word1 in self.entities and word2 in self.entities:
                            pair = tuple(sorted([word1, word2]))
                            context = match.group(0)
                            conjunctionPairs[pair].append({
                                'hymn': hymnRef,
                                'context': context
                            })
        
        print(f"Found {len(conjunctionPairs)} conjunction pairs")
        
        maxConjunctions = max((len(contexts) for contexts in conjunctionPairs.values()), default=1)
        
        for (entity1, entity2), contexts in conjunctionPairs.items():
            relationKey = f"{entity1}||{entity2}"
            normalizedScore = len(contexts) / maxConjunctions
            
            self.relationships[relationKey]['conjunction_score'] = normalizedScore
            self.relationships[relationKey]['conjunction_contexts'] = contexts
        
        return conjunctionPairs
    
    def CalculateHymnCooccurrence(self):
        """Calculate scores for entities appearing in the same hymn"""
        print("\n=== Phase 5: Calculating Hymn Co-occurrence Scores ===")
        
        entityPairs = list(combinations(self.entities.keys(), 2))
        print(f"Analyzing {len(entityPairs)} entity pairs...")
        
        for entity1, entity2 in entityPairs:
            hymns1 = self.entityHymnIndex[entity1]
            hymns2 = self.entityHymnIndex[entity2]
            
            commonHymns = hymns1.intersection(hymns2)
            
            if commonHymns:
                relationKey = f"{entity1}||{entity2}"
                
                cooccurrenceCount = len(commonHymns)
                totalHymns = len(hymns1) + len(hymns2)
                
                normalizedScore = (2 * cooccurrenceCount) / totalHymns
                
                self.relationships[relationKey]['hymn_cooccurrence_score'] = normalizedScore
                self.relationships[relationKey]['hymn_references'] = list(commonHymns)[:10]
                
                self.entityCooccurrence[entity1][entity2] = cooccurrenceCount
                self.entityCooccurrence[entity2][entity1] = cooccurrenceCount
        
        print(f"Found {len(self.relationships)} relationships with hymn co-occurrence")
    
    def CalculateIndirectAssociation(self):
        """Calculate indirect association scores using network analysis"""
        print("\n=== Phase 6: Calculating Indirect Association Scores ===")
        
        entityPairs = list(combinations(self.entities.keys(), 2))
        
        for entity1, entity2 in entityPairs:
            relationKey = f"{entity1}||{entity2}"
            
            if (self.relationships[relationKey]['conjunction_score'] > 0 or 
                self.relationships[relationKey]['hymn_cooccurrence_score'] > 0):
                continue
            
            commonNeighbors = set(self.entityCooccurrence[entity1].keys()).intersection(
                set(self.entityCooccurrence[entity2].keys())
            )
            
            if commonNeighbors:
                indirectScore = 0.0
                for neighbor in commonNeighbors:
                    score1 = self.entityCooccurrence[entity1][neighbor]
                    score2 = self.entityCooccurrence[entity2][neighbor]
                    indirectScore += math.sqrt(score1 * score2)
                
                maxPossible = len(commonNeighbors) * 10
                normalizedScore = min(indirectScore / maxPossible, 1.0) if maxPossible > 0 else 0.0
                
                self.relationships[relationKey]['indirect_score'] = normalizedScore
        
        print("Indirect association calculation complete")
    
    def CalculateFinalScores(self):
        """Combine all scores into final normalized scores"""
        print("\n=== Phase 7: Calculating Final Scores ===")
        
        weights = {
            'conjunction': 0.5,
            'hymn_cooccurrence': 0.3,
            'indirect': 0.2
        }
        
        validRelationships = {}
        
        for relationKey, scores in self.relationships.items():
            finalScore = (
                scores['conjunction_score'] * weights['conjunction'] +
                scores['hymn_cooccurrence_score'] * weights['hymn_cooccurrence'] +
                scores['indirect_score'] * weights['indirect']
            )
            
            scores['final_score'] = round(finalScore, 4)
            
            if finalScore > 0.05:
                validRelationships[relationKey] = scores
        
        self.relationships = validRelationships
        print(f"Final relationships above threshold: {len(self.relationships)}")
        
        return self.relationships
    
    def GenerateRelationshipMatrix(self):
        """Generate the full relationship matrix"""
        print("\n=== Phase 8: Generating Relationship Matrix ===")
        
        entityList = sorted(self.entities.keys())
        matrix = {}
        
        for entity in entityList:
            matrix[entity] = {}
        
        for relationKey, scores in self.relationships.items():
            entity1, entity2 = relationKey.split('||')
            
            matrix[entity1][entity2] = {
                'score': scores['final_score'],
                'conjunction': scores['conjunction_score'],
                'hymn_cooccurrence': scores['hymn_cooccurrence_score'],
                'indirect': scores['indirect_score']
            }
            
            matrix[entity2][entity1] = matrix[entity1][entity2]
        
        with open("relationship_matrix.json", "w", encoding='utf-8') as f:
            json.dump(matrix, f, indent=2, ensure_ascii=False)
        
        print(f"Generated relationship matrix: {len(entityList)}x{len(entityList)}")
        return matrix
    
    def GenerateOptimizedRelationships(self):
        """Generate optimized relationships file for API"""
        print("\n=== Phase 9: Generating Optimized Relationships ===")
        
        optimizedData = []
        
        for relationKey, scores in sorted(self.relationships.items(), 
                                         key=lambda x: x[1]['final_score'], 
                                         reverse=True):
            entity1, entity2 = relationKey.split('||')
            
            optimizedData.append({
                'entity1': entity1,
                'entity2': entity2,
                'score': scores['final_score'],
                'conjunction_score': scores['conjunction_score'],
                'hymn_cooccurrence_score': scores['hymn_cooccurrence_score'],
                'indirect_score': scores['indirect_score'],
                'hymn_references': scores.get('hymn_references', [])[:5],
                'conjunction_contexts': [c['context'] for c in scores.get('conjunction_contexts', [])[:3]]
            })
        
        with open("entity_relationships_optimized.json", "w", encoding='utf-8') as f:
            json.dump(optimizedData, f, indent=2, ensure_ascii=False)
        
        print(f"Generated {len(optimizedData)} optimized relationships")
        return optimizedData
    
    def GenerateMetadata(self):
        """Generate metadata and statistics"""
        print("\n=== Phase 10: Generating Metadata ===")
        
        metadata = {
            'total_entities': len(self.entities),
            'entity_types': {
                'deity': sum(1 for e in self.entities.values() if e['type'] == 'deity'),
                'attribute': sum(1 for e in self.entities.values() if e['type'] == 'attribute')
            },
            'total_relationships': len(self.relationships),
            'score_distribution': {
                'very_high': sum(1 for r in self.relationships.values() if r['final_score'] > 0.7),
                'high': sum(1 for r in self.relationships.values() if 0.5 < r['final_score'] <= 0.7),
                'medium': sum(1 for r in self.relationships.values() if 0.3 < r['final_score'] <= 0.5),
                'low': sum(1 for r in self.relationships.values() if r['final_score'] <= 0.3)
            },
            'top_connected_entities': []
        }
        
        entityConnectionCounts = defaultdict(int)
        for relationKey in self.relationships.keys():
            entity1, entity2 = relationKey.split('||')
            entityConnectionCounts[entity1] += 1
            entityConnectionCounts[entity2] += 1
        
        topConnected = sorted(entityConnectionCounts.items(), 
                            key=lambda x: x[1], reverse=True)[:10]
        
        metadata['top_connected_entities'] = [
            {'entity': entity, 'connections': count} 
            for entity, count in topConnected
        ]
        
        with open("relationship_metadata.json", "w", encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print("\n=== Metadata Summary ===")
        print(f"Total Entities: {metadata['total_entities']}")
        print(f"  - Deities: {metadata['entity_types']['deity']}")
        print(f"  - Attributes: {metadata['entity_types']['attribute']}")
        print(f"Total Relationships: {metadata['total_relationships']}")
        print(f"Score Distribution:")
        print(f"  - Very High (>0.7): {metadata['score_distribution']['very_high']}")
        print(f"  - High (0.5-0.7): {metadata['score_distribution']['high']}")
        print(f"  - Medium (0.3-0.5): {metadata['score_distribution']['medium']}")
        print(f"  - Low (<=0.3): {metadata['score_distribution']['low']}")
        
        return metadata
    
    def BuildCompleteMatrix(self):
        """Run the complete relationship matrix building process"""
        print("=" * 60)
        print("RIGVEDA RELATIONSHIP MATRIX BUILDER")
        print("=" * 60)
        
        self.ExtractNamedEntities()
        self.ClusterSimilarAttributes()
        self.BuildEntityHymnIndex()
        self.CalculateConjunctionScore()
        self.CalculateHymnCooccurrence()
        self.CalculateIndirectAssociation()
        self.CalculateFinalScores()
        self.GenerateRelationshipMatrix()
        self.GenerateOptimizedRelationships()
        self.GenerateMetadata()
        
        print("\n" + "=" * 60)
        print("RELATIONSHIP MATRIX BUILD COMPLETE!")
        print("=" * 60)
        print("\nGenerated Files:")
        print("  1. entities.json - All extracted entities")
        print("  2. attribute_clusters.json - Clustered similar attributes")
        print("  3. relationship_matrix.json - Full NxN relationship matrix")
        print("  4. entity_relationships_optimized.json - Optimized relationships")
        print("  5. relationship_metadata.json - Statistics and metadata")

if __name__ == "__main__":
    builder = RelationshipMatrixBuilder()
    builder.BuildCompleteMatrix()
