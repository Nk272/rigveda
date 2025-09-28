#!/usr/bin/env python3
"""
Rigveda Relationship Analyzer
Analyzes deity relationships in the Rigveda using NLP techniques
Based on the relationship types defined in d_d.txt
"""

import json
import re
from collections import defaultdict
from typing import Set
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from datetime import datetime

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class RigvedaRelationshipAnalyzer:
    def __init__(self, json_file_path: str):
        """Initialize the analyzer with Rigveda data"""
        self.json_file_path = json_file_path
        self.data = None
        self.deities = set()
        self.hymns = []
        self.deity_cooccurrence = defaultdict(int)
        self.deity_epithets = defaultdict(set)
        self.ritual_pairs = set()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Known deity names and their variations
        self.deity_patterns = {
            'Agni': r'\bAgni\b',
            'Indra': r'\bIndra\b',
            'Vāyu': r'\bVāyu\b',
            'Mitra': r'\bMitra\b',
            'Varuṇa': r'\bVaruṇa\b',
            'Soma': r'\bSoma\b',
            'Sūrya': r'\bSūrya\b',
            'Savitṛ': r'\bSavitṛ\b',
            'Aśvins': r'\bAśvins\b',
            'Maruts': r'\bMaruts\b',
            'Viśvedevas': r'\bViśvedevas\b',
            'Sarasvatī': r'\bSarasvatī\b',
            'Dyāvā': r'\bDyāvā\b',
            'Pṛthivī': r'\bPṛthivī\b',
            'Uṣas': r'\bUṣas\b',
            'Tvaṣṭar': r'\bTvaṣṭar\b',
            'Bṛhaspati': r'\bBṛhaspati\b',
            'Pūṣan': r'\bPūṣan\b',
            'Bhaga': r'\bBhaga\b',
            'Vṛtra': r'\bVṛtra\b'
        }
        
        # Known ritual/functional pairs
        self.known_ritual_pairs = [
            ('Mitra', 'Varuṇa'),
            ('Indra', 'Agni'),
            ('Dyāvā', 'Pṛthivī'),
            ('Aśvins', 'Aśvins'),  # Twin deities
            ('Indra', 'Vāyu'),
            ('Sūrya', 'Uṣas'),
            ('Agni', 'Soma')
        ]
        
        # Cosmic domains
        self.cosmic_domains = {
            'storm': ['Indra', 'Maruts', 'Vāyu'],
            'solar': ['Sūrya', 'Savitṛ', 'Uṣas'],
            'fire': ['Agni'],
            'water': ['Varuṇa', 'Soma'],
            'earth': ['Pṛthivī'],
            'sky': ['Dyāvā'],
            'twin': ['Aśvins']
        }
        
        self.load_data()
    
    def load_data(self):
        """Load Rigveda JSON data"""
        print("Loading Rigveda data...")
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Extract all hymns and deities
        for book_num, book_data in self.data['books'].items():
            for hymn_num, hymn_data in book_data['hymns'].items():
                self.hymns.append({
                    'book': book_num,
                    'hymn_number': hymn_num,
                    'text': hymn_data['text'],
                    'title': hymn_data['title']
                })
        
        print(f"Loaded {len(self.hymns)} hymns from {len(self.data['books'])} books")
    
    def extract_deities_from_text(self, text: str) -> Set[str]:
        """Extract deity names from text using pattern matching"""
        found_deities = set()
        
        for deity, pattern in self.deity_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                found_deities.add(deity)
        
        return found_deities
    
    def analyze_textual_cooccurrence(self):
        """1️⃣ Textual Co-occurrence Analysis"""
        print("\n=== 1️⃣ TEXTUAL CO-OCCURRENCE ANALYSIS ===")
        
        cooccurrence_matrix = defaultdict(int)
        sequential_pairs = defaultdict(int)
        
        for hymn in self.hymns:
            deities_in_hymn = self.extract_deities_from_text(hymn['text'])
            
            # Co-invocation: deities praised in same hymn
            deity_list = list(deities_in_hymn)
            for i in range(len(deity_list)):
                for j in range(i + 1, len(deity_list)):
                    pair = tuple(sorted([deity_list[i], deity_list[j]]))
                    cooccurrence_matrix[pair] += 1
            
            # Sequential praise: analyze adjacent mantras (simplified as sentences)
            sentences = re.split(r'[.!?]', hymn['text'])
            for sentence in sentences:
                sentence_deities = self.extract_deities_from_text(sentence)
                if len(sentence_deities) >= 2:
                    deity_list = list(sentence_deities)
                    for i in range(len(deity_list)):
                        for j in range(i + 1, len(deity_list)):
                            pair = tuple(sorted([deity_list[i], deity_list[j]]))
                            sequential_pairs[pair] += 1
        
        # Top co-occurring pairs
        top_pairs = sorted(cooccurrence_matrix.items(), key=lambda x: x[1], reverse=True)[:20]
        print("Top Co-occurring Deity Pairs:")
        for (deity1, deity2), count in top_pairs:
            print(f"  {deity1} - {deity2}: {count} times")
        
        # Top sequential pairs
        top_sequential = sorted(sequential_pairs.items(), key=lambda x: x[1], reverse=True)[:10]
        print("\nTop Sequential Praise Pairs:")
        for (deity1, deity2), count in top_sequential:
            print(f"  {deity1} - {deity2}: {count} times")
        
        return cooccurrence_matrix, sequential_pairs
    
    def analyze_ritual_functional_pairings(self):
        """2️⃣ Ritual/Functional Pairings Analysis"""
        print("\n=== 2️⃣ RITUAL/FUNCTIONAL PAIRINGS ANALYSIS ===")
        
        ritual_analysis = defaultdict(int)
        mythic_allies = defaultdict(int)
        
        for hymn in self.hymns:
            deities_in_hymn = self.extract_deities_from_text(hymn['text'])
            deity_list = list(deities_in_hymn)
            
            # Check for known ritual pairs
            for i in range(len(deity_list)):
                for j in range(i + 1, len(deity_list)):
                    pair = tuple(sorted([deity_list[i], deity_list[j]]))
                    if pair in self.known_ritual_pairs:
                        ritual_analysis[pair] += 1
            
            # Check for mythic allies (known pairs)
            for known_pair in self.known_ritual_pairs:
                if known_pair[0] in deities_in_hymn and known_pair[1] in deities_in_hymn:
                    mythic_allies[known_pair] += 1
        
        print("Ritual/Functional Pairings Found:")
        for pair, count in sorted(ritual_analysis.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pair[0]} - {pair[1]}: {count} times")
        
        print("\nMythic Allies:")
        for pair, count in sorted(mythic_allies.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pair[0]} - {pair[1]}: {count} times")
        
        return ritual_analysis, mythic_allies
    
    def analyze_thematic_domain_similarity(self):
        """3️⃣ Thematic/Domain Similarity Analysis"""
        print("\n=== 3️⃣ THEMATIC/DOMAIN SIMILARITY ANALYSIS ===")
        
        # Extract epithets and descriptions
        epithets = defaultdict(set)
        domain_analysis = defaultdict(list)
        
        for hymn in self.hymns:
            text = hymn['text']
            deities_in_hymn = self.extract_deities_from_text(text)
            
            # Extract epithets (adjectives near deity names)
            for deity in deities_in_hymn:
                # Find epithets near deity names
                deity_pattern = re.escape(deity)
                epithet_pattern = r'(\w+)\s+' + deity_pattern + r'|' + deity_pattern + r'\s+(\w+)'
                matches = re.findall(epithet_pattern, text, re.IGNORECASE)
                
                for match in matches:
                    epithet = match[0] if match[0] else match[1]
                    if len(epithet) > 3:  # Filter out short words
                        epithets[deity].add(epithet.lower())
            
            # Categorize by cosmic domain
            for deity in deities_in_hymn:
                for domain, domain_deities in self.cosmic_domains.items():
                    if deity in domain_deities:
                        domain_analysis[domain].append(hymn)
        
        print("Shared Epithets Analysis:")
        for deity, deity_epithets in epithets.items():
            if len(deity_epithets) > 5:  # Only show deities with many epithets
                print(f"  {deity}: {', '.join(list(deity_epithets)[:10])}")
        
        print("\nCosmic Domain Analysis:")
        for domain, hymns in domain_analysis.items():
            print(f"  {domain.title()} domain: {len(hymns)} hymns")
        
        return epithets, domain_analysis
    
    def analyze_narrative_relationships(self):
        """4️⃣ Narrative Relationships Analysis"""
        print("\n=== 4️⃣ NARRATIVE RELATIONSHIPS ANALYSIS ===")
        
        rivalry_patterns = defaultdict(int)
        kinship_patterns = defaultdict(int)
        
        # Keywords indicating rivalry or tension
        rivalry_keywords = ['slayer', 'destroyer', 'conqueror', 'battle', 'fight', 'oppose', 'challenge']
        kinship_keywords = ['father', 'son', 'brother', 'sister', 'twin', 'born', 'offspring']
        
        for hymn in self.hymns:
            text = hymn['text'].lower()
            deities_in_hymn = self.extract_deities_from_text(hymn['text'])
            
            # Check for rivalry patterns
            for keyword in rivalry_keywords:
                if keyword in text:
                    for deity in deities_in_hymn:
                        rivalry_patterns[deity] += 1
            
            # Check for kinship patterns
            for keyword in kinship_keywords:
                if keyword in text:
                    for deity in deities_in_hymn:
                        kinship_patterns[deity] += 1
        
        print("Rivalry/Tension Patterns:")
        for deity, count in sorted(rivalry_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {deity}: {count} instances")
        
        print("\nKinship Patterns:")
        for deity, count in sorted(kinship_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {deity}: {count} instances")
        
        return rivalry_patterns, kinship_patterns
    
    def analyze_temporal_seasonal_patterns(self):
        """5️⃣ Temporal/Seasonal Patterns Analysis"""
        print("\n=== 5️⃣ TEMPORAL/SEASONAL PATTERNS ANALYSIS ===")
        
        temporal_keywords = {
            'dawn': ['dawn', 'morning', 'sunrise', 'early'],
            'dusk': ['dusk', 'evening', 'sunset', 'late'],
            'seasonal': ['spring', 'summer', 'autumn', 'winter', 'season']
        }
        
        temporal_analysis = defaultdict(lambda: defaultdict(int))
        
        for hymn in self.hymns:
            text = hymn['text'].lower()
            deities_in_hymn = self.extract_deities_from_text(hymn['text'])
            
            for time_period, keywords in temporal_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        for deity in deities_in_hymn:
                            temporal_analysis[time_period][deity] += 1
        
        print("Temporal Patterns:")
        for time_period, deity_counts in temporal_analysis.items():
            print(f"\n{time_period.title()} Deities:")
            for deity, count in sorted(deity_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {deity}: {count} instances")
        
        return temporal_analysis
    
    def analyze_cross_rishi_associations(self):
        """6️⃣ Cross-Rishi Associations Analysis"""
        print("\n=== 6️⃣ CROSS-RISHI ASSOCIATIONS ANALYSIS ===")
        
        # Extract Rishi names from hymn titles
        rishi_deity_associations = defaultdict(set)
        
        for hymn in self.hymns:
            title = hymn['title']
            text = hymn['text']
            deities_in_hymn = self.extract_deities_from_text(text)
            
            # Extract Rishi name from title (simplified)
            rishi_match = re.search(r'HYMN.*?\.\s*([^.]+)\.', title)
            if rishi_match:
                rishi_name = rishi_match.group(1).strip()
                for deity in deities_in_hymn:
                    rishi_deity_associations[rishi_name].add(deity)
        
        print("Rishi-Deity Associations:")
        for rishi, deities in rishi_deity_associations.items():
            if len(deities) > 3:  # Only show Rishis with multiple deity associations
                print(f"  {rishi}: {', '.join(sorted(deities))}")
        
        return rishi_deity_associations
    
    def analyze_semantic_closeness(self):
        """7️⃣ Semantic Closeness Analysis using TF-IDF"""
        print("\n=== 7️⃣ SEMANTIC CLOSENESS ANALYSIS ===")
        
        # Prepare texts for each deity
        deity_texts = defaultdict(list)
        
        for hymn in self.hymns:
            deities_in_hymn = self.extract_deities_from_text(hymn['text'])
            for deity in deities_in_hymn:
                deity_texts[deity].append(hymn['text'])
        
        # Combine texts for each deity
        deity_combined_texts = {}
        for deity, texts in deity_texts.items():
            if len(texts) > 5:  # Only analyze deities with sufficient hymns
                deity_combined_texts[deity] = ' '.join(texts)
        
        if len(deity_combined_texts) < 2:
            print("Insufficient data for semantic analysis")
            return {}
        
        # TF-IDF analysis
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(deity_combined_texts.values())
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        deity_names = list(deity_combined_texts.keys())
        
        # Find most similar deity pairs
        similarities = []
        for i in range(len(deity_names)):
            for j in range(i + 1, len(deity_names)):
                similarity = similarity_matrix[i][j]
                similarities.append((deity_names[i], deity_names[j], similarity))
        
        similarities.sort(key=lambda x: x[2], reverse=True)
        
        print("Most Semantically Similar Deity Pairs:")
        for deity1, deity2, similarity in similarities[:10]:
            print(f"  {deity1} - {deity2}: {similarity:.3f}")
        
        return dict(similarities)
    
    def generate_relationship_network(self, cooccurrence_data):
        """Generate a network graph of deity relationships"""
        print("\n=== GENERATING RELATIONSHIP NETWORK ===")
        
        G = nx.Graph()
        
        # Add nodes and edges based on co-occurrence
        for (deity1, deity2), weight in cooccurrence_data.items():
            if weight > 2:  # Only include significant relationships
                G.add_edge(deity1, deity2, weight=weight)
        
        print(f"Network has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        # Calculate network metrics
        if G.number_of_nodes() > 0:
            centrality = nx.degree_centrality(G)
            top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            
            print("\nMost Central Deities (by degree):")
            for deity, centrality_score in top_central:
                print(f"  {deity}: {centrality_score:.3f}")
        
        return G
    
    def run_complete_analysis(self):
        """Run all relationship analyses"""
        print("🔍 RIGVEDA RELATIONSHIP ANALYSIS")
        print("=" * 50)
        
        # Run all analyses
        cooccurrence_data, sequential_data = self.analyze_textual_cooccurrence()
        ritual_data, mythic_data = self.analyze_ritual_functional_pairings()
        epithets_data, domain_data = self.analyze_thematic_domain_similarity()
        rivalry_data, kinship_data = self.analyze_narrative_relationships()
        temporal_data = self.analyze_temporal_seasonal_patterns()
        rishi_data = self.analyze_cross_rishi_associations()
        semantic_data = self.analyze_semantic_closeness()
        
        # Generate network
        network = self.generate_relationship_network(cooccurrence_data)
        
        # Compile results
        results = {
            'cooccurrence': cooccurrence_data,
            'sequential': sequential_data,
            'ritual': ritual_data,
            'mythic': mythic_data,
            'epithets': epithets_data,
            'domain': domain_data,
            'rivalry': rivalry_data,
            'kinship': kinship_data,
            'temporal': temporal_data,
            'rishi': rishi_data,
            'semantic': semantic_data,
            'network': network
        }
        
        print("\n✅ ANALYSIS COMPLETE")
        return results

def main():
    """Main function to run the analysis"""
    analyzer = RigvedaRelationshipAnalyzer('/Users/nikunjgoyal/Codes/rigveda/rigveda_data.json')
    results = analyzer.run_complete_analysis()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'/Users/nikunjgoyal/Codes/rigveda/rigveda_relationships_{timestamp}.json'
    
    # Convert network to serializable format
    serializable_results = {}
    for key, value in results.items():
        if key == 'network':
            # Convert network to adjacency list
            serializable_results[key] = {
                'nodes': list(value.nodes()),
                'edges': [(u, v, d['weight']) for u, v, d in value.edges(data=True)]
            }
        else:
            serializable_results[key] = dict(value) if isinstance(value, dict) else value
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Results saved to: {output_file}")

if __name__ == "__main__":
    main()
