from enum import Enum
import json
import sqlite3
import re
from typing import Dict, List
from tqdm import tqdm
import spacy

SIMILARITY_THRESHOLD = 0.8

class WordType(Enum):
    STANDARD = "standard"
    NAMED_ENTITY = "named_entity"
    COMBINED_WORD = "combined_word"
    IGNORED = "ignored"

class Word:
    def __init__(self, word: str, frequency: int, mergedWith: List[str], type: WordType, hymn_num: int, book_num: int):
        self.word = word
        self.frequency = frequency
        self.mergedWith = mergedWith
        self.type = type.value
        self.hymn_num = hymn_num
        self.book_num = book_num

class WordProcessor:
    def __init__(self, json_path: str, db_path: str):
        self.json_path = json_path
        self.db_path = db_path
        self.nlp = spacy.load("en_core_web_md")
        self.unfilteredWords = dict()
        self.ignoredWords = []
        self.combinedWords = []
        self.mergedWords = []
        self.includedWords = []
        
        self.commonIgnoreWords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall',
            'that', 'this', 'these', 'those', 'he', 'she', 'it', 'they', 'them',
            'their', 'his', 'her', 'its', 'our', 'your', 'i', 'you', 'we', 'us',
            'him', 'into', 'up', 'down', 'out', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'yet'
        }
        
    def LoadHymnData(self) -> List[str]:
        """Load all hymn texts from JSON"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        hymn_num = 1
        book_num = 1
        for _, book_data in data['books'].items():
            for _, hymn_data in book_data['hymns'].items():
                text=hymn_data['text']
                words=re.findall(r'\b[\w-]+\b', text)
                for word in words:
                    word=word.strip()
                    if word == "":
                        continue
                    if word in self.unfilteredWords.keys():
                        self.unfilteredWords[word].frequency += 1
                    else:
                        self.unfilteredWords[word] = Word(word, 1, None, WordType.STANDARD, hymn_num, book_num)
                hymn_num += 1
            book_num += 1

        self.unfilteredWords = dict(sorted(self.unfilteredWords.items(), key=lambda x: x[1].frequency, reverse=True))
        print(f"Loaded {len(self.unfilteredWords)} unfiltered words")
        return self.unfilteredWords
    
    def IsNamedEntity(self, word: str) -> bool:
        """Check if word is a named entity"""
        doc = self.nlp(word)
        
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'GPE', 'ORG', 'NORP', 'FAC', 'LOC']:
                return True
        
        for token in doc:
            if token.pos_ == 'PROPN':
                return True
        
        return False
    
    def ShouldIgnoreWord(self, word: str) -> bool:
        """Determine if word should be ignored"""
        word_lower = word.lower()
        
        if word_lower in self.commonIgnoreWords:
            return True
        
        if len(word) <= 2 and not word[0].isupper():
            return True
        
        doc = self.nlp(word_lower)
        for token in doc:
            if token.pos_ in ['ADP', 'DET', 'CONJ', 'CCONJ', 'SCONJ', 'PRON', 'AUX']:
                return True
        
        return False
    
    def IsCombinedWord(self, word: str) -> bool:
        """Check if word is a combined word (hyphenated)"""
        return '-' in word and word.count('-') >= 1
    
    def NormalizeWord(self, word: str) -> str:
        """Normalize word by removing possessive and punctuation"""
        word = re.sub(r"['']s$", '', word)
        word = re.sub(r'[.,;:!?"]', '', word)
        return word
    
    def AreSimilarWords(self, word1: str, word2: str, semanticCheck: bool = True) -> bool:
        """Check if two words are similar (for merging)"""
        word1_norm = self.NormalizeWord(word1.lower())
        word2_norm = self.NormalizeWord(word2.lower())
        
        if word1_norm == word2_norm:
            return True
        
        if word1_norm.endswith('s') and word1_norm[:-1] == word2_norm:
            return True
        if word2_norm.endswith('s') and word2_norm[:-1] == word1_norm:
            return True

        if not semanticCheck:
            return False

        doc1 = self.nlp(word1_norm)
        doc2 = self.nlp(word2_norm)
        if doc1 and doc2 and doc1.vector_norm and doc2.vector_norm:
            similarity = doc1.similarity(doc2)
            return similarity >= SIMILARITY_THRESHOLD
        return False
    
    def ProcessWords(self, wordList: Dict[str, Word]):
        """Process all words and categorize them"""
        
        for word in tqdm(wordList):
            wordObj = wordList[word]
            wordStr = wordObj.word

            # Set the type of the word
            semanticCheck = True
            if self.IsCombinedWord(wordStr):
                wordObj.type = WordType.COMBINED_WORD.value
                self.combinedWords.append(wordObj)
                continue
            elif self.IsNamedEntity(word):
                wordObj.type = WordType.NAMED_ENTITY.value
                semanticCheck = False
            elif self.ShouldIgnoreWord(wordStr):
                wordObj.type = WordType.IGNORED.value
                self.ignoredWords.append(wordObj)
                continue
            else:
                wordObj.type = WordType.STANDARD.value

            merged = False
            
            for existingWord in self.includedWords:
                if self.AreSimilarWords(wordStr, existingWord.word, semanticCheck):
                    existingWord.frequency += wordObj.frequency
                    wordObj.mergedWith = existingWord.word
                    self.mergedWords.append(wordObj)
                    merged = True
                    break
            
            if not merged:
                self.includedWords.append(wordObj)
            else:
                self.mergedWords.append(wordObj)
        
        self.includedWords = sorted(self.includedWords, key=lambda x: x.frequency, reverse=True)
        self.mergedWords = sorted(self.mergedWords, key=lambda x: x.frequency, reverse=True)
        self.ignoredWords = sorted(self.ignoredWords, key=lambda x: x.frequency, reverse=True)
        self.combinedWords = sorted(self.combinedWords, key=lambda x: x.frequency, reverse=True)
        print(f"Included words: {len(self.includedWords)}")
        print(f"Ignored words: {len(self.ignoredWords)}")
        print(f"Combined words: {len(self.combinedWords)}")
        print(f"Merged words: {len(self.mergedWords)}")

        if len(self.includedWords) + len(self.ignoredWords) + len(self.combinedWords) + len(self.mergedWords) != len(self.unfilteredWords):
            print(f"Error: {len(self.includedWords) + len(self.ignoredWords) + len(self.combinedWords) + len(self.mergedWords)} != {len(self.unfilteredWords)}")
        
        return self.includedWords

    def CreateDatabase(self):
        """Create SQLite database with three tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DROP TABLE IF EXISTS included_words')
        cursor.execute('DROP TABLE IF EXISTS ignored_words')
        cursor.execute('DROP TABLE IF EXISTS combined_words')
        
        cursor.execute('''
            CREATE TABLE included_words (
                word TEXT PRIMARY KEY,
                frequency INTEGER,
                merged_with TEXT,
                word_type TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE ignored_words (
                word TEXT PRIMARY KEY
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE combined_words (
                word TEXT PRIMARY KEY,
                frequency INTEGER,
                parts TEXT
            )
        ''')
        
        for word, data in self.includedWords.items():
            merged_with = ','.join(data['mergedWith']) if data['mergedWith'] else ''
            cursor.execute(
                'INSERT INTO included_words VALUES (?, ?, ?, ?)',
                (word, data['frequency'], merged_with, data['type'])
            )
        
        for word in self.ignoredWords:
            cursor.execute('INSERT INTO ignored_words VALUES (?)', (word,))
        
        for word, data in self.combinedWords.items():
            parts = ','.join(data['parts'])
            cursor.execute(
                'INSERT INTO combined_words VALUES (?, ?, ?)',
                (word, data['frequency'], parts)
            )
        
        conn.commit()
        conn.close()
    
    def Run(self):
        """Main processing pipeline"""
        print("="*80)
        print("RIGVEDA WORD PROCESSOR")
        print("="*80)
        
        print("\n[1/4] Loading hymn data...")
        texts = self.LoadHymnData()
        print(f"      Loaded {len(texts)} hymns")
        
        print("\n[2/4] Extracting words...")
        wordFreq = self.ExtractWords(texts)
        totalWords = sum(wordFreq.values())
        print(f"      Found {len(wordFreq)} unique words")
        print(f"      Total word occurrences: {totalWords:,}")
        
        print("\n[3/4] Processing and categorizing words...")
        self.ProcessWords(wordFreq)
        
        print("\n[4/4] Creating database...")
        self.CreateDatabase()
        print(f"      Database created at: {self.db_path}")
        
        self.PrintStatistics(wordFreq)
    
    def PrintStatistics(self, wordFreq):
        """Print detailed statistics"""
        totalUnique = len(wordFreq)
        totalOccurrences = sum(wordFreq.values())
        
        includedCount = len(self.includedWords)
        ignoredCount = len(self.ignoredWords)
        combinedCount = len(self.combinedWords)
        
        includedOccurrences = sum(d['frequency'] for d in self.includedWords.values())
        ignoredOccurrences = sum(wordFreq[w] for w in self.ignoredWords if w in wordFreq)
        combinedOccurrences = sum(d['frequency'] for d in self.combinedWords.values())
        
        namedEntityCount = sum(1 for d in self.includedWords.values() if d['type'] == 'named_entity')
        semanticGroupCount = sum(1 for d in self.includedWords.values() if d['type'] == 'semantic_group')
        standardCount = sum(1 for d in self.includedWords.values() if d['type'] == 'standard')
        
        totalMerged = sum(len(d['mergedWith']) for d in self.includedWords.values())
        
        print("\n" + "="*80)
        print("FINAL STATISTICS")
        print("="*80)
        
        print(f"\nINPUT:")
        print(f"  Total unique words extracted:      {totalUnique:>6}")
        print(f"  Total word occurrences:             {totalOccurrences:>6,}")
        
        print(f"\nOUTPUT - CATEGORIZATION:")
        print(f"  Included Words:                     {includedCount:>6}  ({includedCount/totalUnique*100:>5.1f}%)  [{includedOccurrences:>6,} occurrences]")
        print(f"    ├─ Named Entities:                {namedEntityCount:>6}")
        print(f"    ├─ Semantic Groups:               {semanticGroupCount:>6}")
        print(f"    └─ Standard Words:                {standardCount:>6}")
        print(f"\n  Ignored Words:                      {ignoredCount:>6}  ({ignoredCount/totalUnique*100:>5.1f}%)  [{ignoredOccurrences:>6,} occurrences]")
        print(f"\n  Combined/Hyphenated Words:          {combinedCount:>6}  ({combinedCount/totalUnique*100:>5.1f}%)  [{combinedOccurrences:>6,} occurrences]")
        
        print(f"\nMERGING DETAILS:")
        print(f"  Total variants merged:              {totalMerged:>6}")
        wordsWithMerges = sum(1 for d in self.includedWords.values() if len(d['mergedWith']) > 0)
        print(f"  Words with merged variants:         {wordsWithMerges:>6}")
        
        print(f"\nVERIFICATION:")
        print(f"  Sum of categories:                  {includedCount + ignoredCount + combinedCount:>6}")
        print(f"  Expected (total unique):            {totalUnique:>6}")
        print(f"  Match: {'✓' if includedCount + ignoredCount + combinedCount == totalUnique else '✗'}")
        
        print("\n" + "="*80)
        print("TOP 15 INCLUDED WORDS (by frequency)")
        print("="*80)
        sortedIncluded = sorted(self.includedWords.items(), key=lambda x: x[1]['frequency'], reverse=True)
        print(f"{'Word':<25} {'Frequency':<12} {'Type':<20} {'Merged'}")
        print("-"*80)
        for word, data in sortedIncluded[:15]:
            mergedInfo = f"({len(data['mergedWith'])} variants)" if data['mergedWith'] else ""
            print(f"{word:<25} {data['frequency']:<12} {data['type']:<20} {mergedInfo}")
        
        print("\n" + "="*80)
        print("TOP 10 COMBINED WORDS (hyphenated)")
        print("="*80)
        sortedCombined = sorted(self.combinedWords.items(), key=lambda x: x[1]['frequency'], reverse=True)
        print(f"{'Word':<35} {'Frequency':<12} {'Parts'}")
        print("-"*80)
        for word, data in sortedCombined[:10]:
            parts = ' + '.join(data['parts'])
            print(f"{word:<35} {data['frequency']:<12} {parts}")
        
        print("\n" + "="*80)

if __name__ == '__main__':
    processor = WordProcessor(
        json_path='/Users/nikunjgoyal/Codes/rigveda/rigveda_data.json',
        db_path='/Users/nikunjgoyal/Codes/rigveda/word_list.db'
    )
    processor.Run()
