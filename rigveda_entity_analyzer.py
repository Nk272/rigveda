import json
import re
from collections import Counter, defaultdict
import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

class RigvedaEntityAnalyzer:
    def __init__(self, data_file="rigveda_data.json"):
        with open(data_file, "r", encoding='utf-8') as file:
            self.data = json.load(file)
        
        self.stopwords = set()
        self.word_frequencies = Counter()
        self.entity_relationships = defaultdict(list)
        self.deity_mentions = defaultdict(list)
        self.word_hymns = defaultdict(list)
        self.word_groups = defaultdict(list)  # Groups of similar words
        self.merged_frequencies = Counter()   # Frequencies after merging
        self.lemmatizer = WordNetLemmatizer()
        
        # Download required NLTK data
        try:
            nltk.data.find('corpora/wordnet')
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("Downloading NLTK data...")
            nltk.download('wordnet')
            nltk.download('punkt')
            nltk.download('omw-1.4')

    def write_to_json(self, filename, data):
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        with open(filename, "w", encoding='utf-8') as file:
            json.dump(sorted_data, file, indent=2, ensure_ascii=False)
        
    def CleanWord(self, word):
        """Clean and normalize words"""
        word = word.lower().strip().strip(".,!?\"'():-_")
        return word if len(word) > 1 else None
    
    def GetWordNetSimilarity(self, word1, word2):
        """Calculate semantic similarity using WordNet"""
        synsets1 = wordnet.synsets(word1)
        synsets2 = wordnet.synsets(word2)
        
        if not synsets1 or not synsets2:
            # For Sanskrit words not in WordNet, use string similarity as fallback
            return self.GetStringSimilarity(word1, word2)
        
        max_similarity = 0.0
        for syn1 in synsets1:
            for syn2 in synsets2:
                try:
                    # Use path similarity as primary measure
                    similarity = syn1.path_similarity(syn2)
                    if similarity is not None:
                        max_similarity = max(max_similarity, similarity)
                except:
                    continue
        
        return max_similarity
    
    def GetStringSimilarity(self, word1, word2):
        """Fallback string similarity for words not in WordNet"""
        # Simple character-based similarity
        if word1 == word2:
            return 1.0
        
        # Check for common prefixes/suffixes
        common_chars = sum(1 for c1, c2 in zip(word1, word2) if c1 == c2)
        max_len = max(len(word1), len(word2))
        if max_len == 0:
            return 0.0
        
        return common_chars / max_len
    
    def GetLemmatizedForm(self, word):
        """Get the lemmatized form of a word"""
        try:
            return self.lemmatizer.lemmatize(word)
        except:
            return word
    
    def AreSemanticallyRelated(self, word1, word2):
        """Check if two words are semantically related using multiple NLTK methods"""
        # Method 1: Direct WordNet similarity
        wordnet_sim = self.GetWordNetSimilarity(word1, word2)
        
        # Method 2: Check if one is the lemma of the other
        lemma1 = self.GetLemmatizedForm(word1)
        lemma2 = self.GetLemmatizedForm(word2)
        lemma_match = (lemma1 == lemma2) or (lemma1 == word2) or (lemma2 == word1)
        
        # Method 3: Check for morphological variations
        morph_variations = self.CheckMorphologicalVariations(word1, word2)
        
        # Method 4: Check for compound word relationships
        compound_relation = self.CheckCompoundRelationship(word1, word2)
        
        # Method 5: Check for antonym/synonym relationships
        semantic_relation = self.CheckSemanticRelations(word1, word2)
        
        # Combine all methods
        similarity_score = (
            wordnet_sim * 0.4 +
            (1.0 if lemma_match else 0.0) * 0.3 +
            (1.0 if morph_variations else 0.0) * 0.15 +
            (1.0 if compound_relation else 0.0) * 0.1 +
            (1.0 if semantic_relation else 0.0) * 0.05
        )
        
        return similarity_score
    
    def CheckMorphologicalVariations(self, word1, word2):
        """Check for morphological variations (plurals, tenses, etc.)"""
        # Common morphological patterns
        patterns = [
            (word1 + 's', word2), (word1, word2 + 's'),
            (word1 + 'ed', word2), (word1, word2 + 'ed'),
            (word1 + 'ing', word2), (word1, word2 + 'ing'),
            (word1 + 'er', word2), (word1, word2 + 'er'),
            (word1 + 'est', word2), (word1, word2 + 'est'),
            (word1 + 'ly', word2), (word1, word2 + 'ly'),
        ]
        
        for pattern1, pattern2 in patterns:
            if pattern1 == word2 or pattern2 == word1:
                return True
        return False
    
    def CheckCompoundRelationship(self, word1, word2):
        """Check if words are related through compound word formation"""
        # Check if one word contains the other
        if word1 in word2 or word2 in word1:
            return True
        
        # Check for hyphenated compound patterns
        if '-' in word1 and word2 in word1.split('-'):
            return True
        if '-' in word2 and word1 in word2.split('-'):
            return True
        
        return False
    
    def CheckSemanticRelations(self, word1, word2):
        """Check for direct semantic relationships in WordNet"""
        synsets1 = wordnet.synsets(word1)
        synsets2 = wordnet.synsets(word2)
        
        for syn1 in synsets1:
            for syn2 in synsets2:
                # Check for direct relationships
                if syn1 == syn2:
                    return True
                
                # Check for hypernym/hyponym relationships
                if syn1 in syn2.hypernyms() or syn2 in syn1.hypernyms():
                    return True
                if syn1 in syn2.hyponyms() or syn2 in syn1.hyponyms():
                    return True
                
                # Check for meronym/holonym relationships
                if syn1 in syn2.part_meronyms() or syn2 in syn1.part_meronyms():
                    return True
                if syn1 in syn2.substance_meronyms() or syn2 in syn1.substance_meronyms():
                    return True
        
        return False
    
    def CalculateSimilarity(self, word1, word2):
        """Calculate semantic similarity using NLTK methods"""
        return self.AreSemanticallyRelated(word1, word2)
    
    def FindSemanticGroups(self, threshold=0.75):
        """Group semantically similar words together"""
        words = list(self.word_frequencies.keys())
        processed = set()
        groups = []
        
        for i, word1 in enumerate(words):
            if word1 in processed:
                continue
                
            current_group = [word1]
            processed.add(word1)
            
            for j, word2 in enumerate(words[i+1:], i+1):
                if word2 in processed:
                    continue
                    
                similarity = self.CalculateSimilarity(word1, word2)
                
                if similarity >= threshold:
                    current_group.append(word2)
                    processed.add(word2)
            
            if len(current_group) > 1:
                groups.append(current_group)
        
        return groups
    
    def MergeSimilarWords(self, threshold=0.75):
        """Merge semantically similar words and create word groups"""
        print("Finding semantic groups...")
        groups = self.FindSemanticGroups(threshold)
        
        # Create word groups mapping
        for group in groups:
            # Use the most frequent word as the main word
            main_word = max(group, key=lambda w: self.word_frequencies[w])
            
            # Add all words in group to the main word's group
            self.word_groups[main_word] = group
            
            # Calculate merged frequency
            total_frequency = sum(self.word_frequencies[word] for word in group)
            self.merged_frequencies[main_word] = total_frequency
            
            print(f"Group: {main_word} <- {group} (total freq: {total_frequency})")
        
        # Add non-grouped words to merged frequencies
        all_grouped_words = set()
        for group in groups:
            all_grouped_words.update(group)
        
        for word, freq in self.word_frequencies.items():
            if word not in all_grouped_words:
                self.merged_frequencies[word] = freq
        
        # Save word groups
        with open("word_groups.json", "w", encoding='utf-8') as file:
            json.dump(dict(self.word_groups), file, indent=2, ensure_ascii=False)
        
        # Save merged frequencies
        with open("merged_frequencies.json", "w", encoding='utf-8') as file:
            sorted_merged = dict(sorted(self.merged_frequencies.items(), 
                                     key=lambda x: x[1], reverse=True))
            json.dump(sorted_merged, file, indent=2, ensure_ascii=False)
        
        print(f"Created {len(groups)} semantic groups")
        return groups
    
    def ExtractAllWords(self):
        """Extract all words from the Rigveda texts"""
        for _, book in self.data['books'].items():
            for _, hymn in book['hymns'].items():
                text = hymn['text']
                words = text.split()
                ref = f"Book {book['book_number']}, Hymn {hymn['hymn_number']}"
                
                for word in words:
                    cleaned = self.CleanWord(word)
                    if cleaned and cleaned not in self.stopwords:
                        self.word_frequencies[cleaned] += 1
                        self.word_hymns[cleaned].append(ref)
        self.write_to_json("word_frequencies.json", self.word_frequencies)
        self.write_to_json("word_hymns.json", self.word_hymns)
    
    def CreateCustomStopwords(self):
        """Create custom stopwords based on frequency and common English words"""
        # Common English stopwords
        common_stopwords = {
            'the', 'of', 'and', 'to', 'with', 'in', 'who', 'us', 'for', 'thou', 'o',
            'a', 'he', 'as', 'our', 'his', 'is', 'all', 'thy', 'thee', 'that', 'him',
            'ye', 'we', 'me', 'this', 'from', 'be', 'have', 'on', 'by', 'at', 'or',
            'but', 'not', 'so', 'if', 'when', 'where', 'how', 'what', 'which', 'why',
            'can', 'will', 'shall', 'may', 'must', 'should', 'would', 'could',
            'do', 'does', 'did', 'done', 'get', 'got', 'give', 'gave', 'given',
            'take', 'took', 'taken', 'make', 'made', 'come', 'came', 'go', 'went',
            'see', 'saw', 'seen', 'know', 'knew', 'known', 'think', 'thought',
            'say', 'said', 'tell', 'told', 'ask', 'asked', 'want', 'wanted',
            'need', 'needed', 'use', 'used', 'work', 'worked', 'try', 'tried',
            'find', 'found', 'look', 'looked', 'seem', 'seemed', 'feel', 'felt',
            'become', 'became', 'leave', 'left', 'put', 'call', 'called',
            'turn', 'turned', 'move', 'moved', 'live', 'lived', 'help', 'helped',
            'show', 'showed', 'play', 'played', 'run', 'ran', 'open', 'opened',
            'close', 'closed', 'start', 'started', 'stop', 'stopped', 'end', 'ended',
            'begin', 'began', 'begun', 'continue', 'continued', 'change', 'changed',
            'keep', 'kept', 'let', 'allow', 'allowed', 'follow', 'followed',
            'turn', 'turned', 'move', 'moved', 'live', 'lived', 'help', 'helped'
        }
        custom_stopwords = {
            'their', 'through', 'them', 'it', 'my', 'might', 'whom', 'man'
            'hath',
            'like',
            'they',
            'your',
            'are',
            'men',
            'these',
            'one',
            'forth',
            'you',
            'most',
            'bring',
            'art',
        }

        # Add short words (1-2 characters)
        short_words = {word for word in self.word_frequencies.keys() if len(word) <= 2}
        
        # Combine all stopwords
        self.stopwords = common_stopwords.union(custom_stopwords).union(short_words)    
        print(f"Created custom stopwords list with {len(self.stopwords)} words")
        return self.stopwords
    
    def IdentifyImportantWords(self, top_n=250):
        """Identify the most important words excluding stopwords"""
        # Use merged frequencies if available, otherwise use original frequencies
        frequencies_to_use = self.merged_frequencies if self.merged_frequencies else self.word_frequencies
        
        # Filter out stopwords
        important_words = {word: count for word, count in frequencies_to_use.items() 
                          if word not in self.stopwords and len(word) > 2}
        
        # Sort by frequency
        sorted_important = sorted(important_words.items(), 
                               key=lambda x: x[1], reverse=True)
        
        # Take top N words
        top_words = dict(sorted_important[:top_n])
        
        # Save important words
        with open("important_words.txt", "w", encoding='utf-8') as file:
            file.write(f"Top {top_n} Most Important Words (Stopwords Filtered, Merged):\n")
            file.write("=" * 60 + "\n\n")
            
            for i, (word, freq) in enumerate(sorted_important[:top_n], 1):
                file.write(f"{i:3d}. {word:<25} - {freq:>6} occurrences\n")
        
        print(f"Identified {len(top_words)} important words")
        return top_words
    
    def ExtractDeityNames(self):
        """Extract deity names from hymn titles"""
        deity_frequency = Counter()
        
        for book_num, book in self.data['books'].items():
            for hymn_num, hymn in book['hymns'].items():
                title = hymn['title']
                ref = f"Book {book['book_number']}, Hymn {hymn['hymn_number']}"
                
                # Extract deity name from title (usually after "HYMN X.")
                title_parts = title.split()
                if len(title_parts) >= 3:
                    deity = title_parts[2].strip(".")
                    deity_frequency[deity] += 1
                    self.deity_mentions[deity].append(ref)
        
        # Save deity analysis
        with open("deity_analysis.txt", "w", encoding='utf-8') as file:
            file.write("Deity Analysis from Hymn Titles:\n")
            file.write("=" * 40 + "\n\n")
            
            sorted_deities = sorted(deity_frequency.items(), 
                                  key=lambda x: x[1], reverse=True)
            
            for deity, count in sorted_deities:
                file.write(f"{deity:<20} - {count:>4} hymns\n")
        
        return dict(sorted_deities)
    
    def ExtractEntityRelationships(self, important_words, deities):
        """Extract relationships between important words and entities"""
        relationships = defaultdict(lambda: defaultdict(list))
        
        for book_num, book in self.data['books'].items():
            for hymn_num, hymn in book['hymns'].items():
                text = hymn['text']
                ref = f"Book {book['book_number']}, Hymn {hymn['hymn_number']}"
                
                # Get deity from title
                title_parts = hymn['title'].split()
                deity = title_parts[2].strip(".") if len(title_parts) >= 3 else "UNKNOWN"
                
                # Find co-occurrences of important words with deities
                words_in_hymn = [self.CleanWord(word) for word in text.split()]
                words_in_hymn = [w for w in words_in_hymn if w and w in important_words]
                
                for word in words_in_hymn:
                    relationships[deity][word].append(ref)
        
        # Save relationships
        with open("entity_relationships.json", "w", encoding='utf-8') as file:
            # Convert defaultdict to regular dict for JSON serialization
            relationships_dict = {deity: dict(word_refs) 
                                for deity, word_refs in relationships.items()}
            json.dump(relationships_dict, file, indent=2, ensure_ascii=False)
        
        # Create summary report
        with open("relationship_summary.txt", "w", encoding='utf-8') as file:
            file.write("Entity-Word Relationship Summary:\n")
            file.write("=" * 40 + "\n\n")
            
            for deity in sorted(relationships.keys()):
                file.write(f"\n{deity}:\n")
                deity_words = relationships[deity]
                sorted_words = sorted(deity_words.items(), 
                                    key=lambda x: len(x[1]), reverse=True)
                
                for word, refs in sorted_words[:10]:  # Top 10 words per deity
                    file.write(f"  {word:<20} - {len(refs):>3} co-occurrences\n")
        
        return relationships
    
    def RunAnalysis(self):
        """Run the complete analysis"""
        print("Starting Rigveda Entity Analysis...")
        
        print("Creating custom stopwords...")
        self.CreateCustomStopwords()

        print("Extracting all words...")
        self.ExtractAllWords()
        print(f"Found {len(self.word_frequencies)} unique words")
        
        print("Merging semantically similar words...")
        self.MergeSimilarWords(threshold=0.75)
        
        print("Identifying important words...")
        important_words = self.IdentifyImportantWords(250)
        
        print("Extracting deity names...")
        deities = self.ExtractDeityNames()
        
        print("Extracting entity relationships...")
        relationships = self.ExtractEntityRelationships(important_words, deities)
        
        print("Analysis complete! Check the generated files:")
        print("- custom_stopwords.txt")
        print("- important_words.txt") 
        print("- deity_analysis.txt")
        print("- entity_relationships.json")
        print("- relationship_summary.txt")
        print("- word_groups.json")
        print("- merged_frequencies.json")

if __name__ == "__main__":
    analyzer = RigvedaEntityAnalyzer()
    analyzer.RunAnalysis()
