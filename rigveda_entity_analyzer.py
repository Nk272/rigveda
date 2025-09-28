import json
import re
from collections import Counter, defaultdict

class RigvedaEntityAnalyzer:
    def __init__(self, data_file="rigveda_data.json"):
        with open(data_file, "r", encoding='utf-8') as file:
            self.data = json.load(file)
        
        self.stopwords = set()
        self.word_frequencies = Counter()
        self.entity_relationships = defaultdict(list)
        self.deity_mentions = defaultdict(list)
        self.word_hymns = defaultdict(list)

    def write_to_json(self, filename, data):
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        with open(filename, "w", encoding='utf-8') as file:
            json.dump(sorted_data, file, indent=2, ensure_ascii=False)
        
    def CleanWord(self, word):
        """Clean and normalize words"""
        word = word.lower().strip().strip(".,!?\"'():-_")
        return word if len(word) > 1 else None
    
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
        # Filter out stopwords
        important_words = {word: count for word, count in self.word_frequencies.items() 
                          if word not in self.stopwords and len(word) > 2}
        
        # Sort by frequency
        sorted_important = sorted(important_words.items(), 
                               key=lambda x: x[1], reverse=True)
        
        # Take top N words
        top_words = dict(sorted_important[:top_n])
        
        # Save important words
        with open("important_words.txt", "w", encoding='utf-8') as file:
            file.write(f"Top {top_n} Most Important Words (Stopwords Filtered):\n")
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
        
        
        # print("Identifying important words...")
        # important_words = self.IdentifyImportantWords(250)
        
        # # Step 4: Extract deity names
        # print("Extracting deity names...")
        # deities = self.ExtractDeityNames()
        
        # # Step 5: Extract relationships
        # print("Extracting entity relationships...")
        # relationships = self.ExtractEntityRelationships(important_words, deities)
        
        # print("Analysis complete! Check the generated files:")
        # print("- custom_stopwords.txt")
        # print("- important_words.txt") 
        # print("- deity_analysis.txt")
        # print("- entity_relationships.json")
        # print("- relationship_summary.txt")

if __name__ == "__main__":
    analyzer = RigvedaEntityAnalyzer()
    analyzer.RunAnalysis()
