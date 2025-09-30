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
    def __init__(self, word: str, frequency: int, mergedWith: List[str], type: WordType, hymn_num: int, book_num: int, nlp: spacy.Language):
        self.word = word
        self.frequency = frequency
        self.mergedWith = mergedWith
        self.type = type.value
        self.hymn_num = hymn_num
        self.book_num = book_num
        self.wordnlp = nlp

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

    def NormalizeWord(self, word: str) -> str:
        """Normalize word by removing possessive and punctuation"""
        word = word.lower().strip()
        word = re.sub(r"['']s$", '', word)
        word = re.sub(r'[.,;:!?"]', '', word)
        return word
        
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
                    word=self.NormalizeWord(word)
                    if word == "":
                        continue
                    if word in self.unfilteredWords.keys():
                        self.unfilteredWords[word].frequency += 1
                    else:
                        self.unfilteredWords[word] = Word(word, 1, None, WordType.STANDARD, hymn_num, book_num, self.nlp(word))
                hymn_num += 1
            book_num += 1

        self.unfilteredWords = dict(sorted(self.unfilteredWords.items(), key=lambda x: x[1].frequency, reverse=True))
        print(f"Loaded {len(self.unfilteredWords)} unfiltered words")
        return self.unfilteredWords
    
    def IsNamedEntity(self, word: Word) -> bool:
        """Check if word is a named entity"""
        doc = word.wordnlp
        
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'GPE', 'ORG', 'NORP', 'FAC', 'LOC']:
                return True
        
        for token in doc:
            if token.pos_ == 'PROPN':
                return True
        
        return False
    
    def ShouldIgnoreWord(self, word: Word) -> bool:
        """Determine if word should be ignored"""
        if word.word in self.commonIgnoreWords:
            return True
        
        if len(word.word) <= 2 and not word.word[0].isupper():
            return True
        
        doc = word.wordnlp
        for token in doc:
            if token.pos_ in ['ADP', 'DET', 'CONJ', 'CCONJ', 'SCONJ', 'PRON', 'AUX']:
                return True
        
        return False
    
    def IsCombinedWord(self, word: Word) -> bool:
        """Check if word is a combined word (hyphenated)"""
        return '-' in word.word and word.word.count('-') >= 1
    
    def AreSimilarWords(self, word1: Word, word2: Word, semanticCheck: bool = True) -> bool:
        """Check if two words are similar (for merging)"""
        
        if word1.word == word2.word:
            return True
        
        if word1.word.endswith('s') and word1.word[:-1] == word2.word:
            return True
        if word2.word.endswith('s') and word2.word[:-1] == word1.word:
            return True

        if not semanticCheck:
            return False

        doc1 = word1.wordnlp
        doc2 = word2.wordnlp
        if doc1 and doc2 and doc1.vector_norm and doc2.vector_norm:
            similarity = doc1.similarity(doc2)
            return similarity >= SIMILARITY_THRESHOLD
        return False
    
    def ProcessWords(self, wordList: Dict[str, Word]):
        """Process all words and categorize them"""
        
        for word in tqdm(wordList):
            wordObj = wordList[word]

            # Set the type of the word
            semanticCheck = True
            if self.IsCombinedWord(wordObj):
                wordObj.type = WordType.COMBINED_WORD.value
                self.combinedWords.append(wordObj)
                continue
            elif self.IsNamedEntity(wordObj):
                wordObj.type = WordType.NAMED_ENTITY.value
                semanticCheck = False
            elif self.ShouldIgnoreWord(wordObj):
                wordObj.type = WordType.IGNORED.value
                self.ignoredWords.append(wordObj)
                continue
            else:
                wordObj.type = WordType.STANDARD.value

            merged = False
            
            for existingWord in self.includedWords:
                if self.AreSimilarWords(wordObj, existingWord, semanticCheck):
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
        """Create SQLite database with four tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DROP TABLE IF EXISTS included_words')
        cursor.execute('DROP TABLE IF EXISTS ignored_words')
        cursor.execute('DROP TABLE IF EXISTS combined_words')
        cursor.execute('DROP TABLE IF EXISTS merged_words')
        
        cursor.execute('''
            CREATE TABLE included_words (
                word TEXT PRIMARY KEY,
                frequency INTEGER,
                word_type TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE ignored_words (
                word TEXT PRIMARY KEY,
                frequency INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE combined_words (
                word TEXT PRIMARY KEY,
                frequency INTEGER,
                parts TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE merged_words (
                word TEXT PRIMARY KEY,
                merged_into TEXT,
                frequency INTEGER
            )
        ''')
        
        for wordObj in self.includedWords:
            cursor.execute(
                'INSERT INTO included_words VALUES (?, ?, ?)',
                (wordObj.word, wordObj.frequency, wordObj.type)
            )
        
        for wordObj in self.ignoredWords:
            cursor.execute(
                'INSERT INTO ignored_words VALUES (?, ?)',
                (wordObj.word, wordObj.frequency)
            )
        
        for wordObj in self.combinedWords:
            parts = ','.join(wordObj.word.split('-'))
            cursor.execute(
                'INSERT INTO combined_words VALUES (?, ?, ?)',
                (wordObj.word, wordObj.frequency, parts)
            )
        
        for wordObj in self.mergedWords:
            cursor.execute(
                'INSERT INTO merged_words VALUES (?, ?, ?)',
                (wordObj.word, wordObj.mergedWith, wordObj.frequency)
            )
        
        conn.commit()
        conn.close()
 
    def PrintStatistics(self, unfilteredWords):
        """Print detailed statistics"""
        totalUnique = len(unfilteredWords)
        totalOccurrences = sum(w.frequency for w in unfilteredWords.values())
        
        includedCount = len(self.includedWords)
        ignoredCount = len(self.ignoredWords)
        combinedCount = len(self.combinedWords)
        mergedCount = len(self.mergedWords)
        
        includedOccurrences = sum(w.frequency for w in self.includedWords)
        ignoredOccurrences = sum(w.frequency for w in self.ignoredWords)
        combinedOccurrences = sum(w.frequency for w in self.combinedWords)
        mergedOccurrences = sum(w.frequency for w in self.mergedWords)
        
        namedEntityCount = sum(1 for w in self.includedWords if w.type == WordType.NAMED_ENTITY.value)
        standardCount = sum(1 for w in self.includedWords if w.type == WordType.STANDARD.value)
        
        mergedIntoCount = {}
        for w in self.mergedWords:
            if w.mergedWith not in mergedIntoCount:
                mergedIntoCount[w.mergedWith] = 0
            mergedIntoCount[w.mergedWith] += 1
        
        print("\n" + "="*80)
        print("FINAL STATISTICS")
        print("="*80)
        
        print(f"\nINPUT:")
        print(f"  Total unique words extracted:      {totalUnique:>6}")
        print(f"  Total word occurrences:             {totalOccurrences:>6,}")
        
        print(f"\nOUTPUT - CATEGORIZATION:")
        print(f"  Included Words:                     {includedCount:>6}  ({includedCount/totalUnique*100:>5.1f}%)  [{includedOccurrences:>6,} occurrences]")
        print(f"    ├─ Named Entities:                {namedEntityCount:>6}")
        print(f"    └─ Standard Words:                {standardCount:>6}")
        print(f"\n  Ignored Words:                      {ignoredCount:>6}  ({ignoredCount/totalUnique*100:>5.1f}%)  [{ignoredOccurrences:>6,} occurrences]")
        print(f"\n  Combined/Hyphenated Words:          {combinedCount:>6}  ({combinedCount/totalUnique*100:>5.1f}%)  [{combinedOccurrences:>6,} occurrences]")
        print(f"\n  Merged Words:                       {mergedCount:>6}  ({mergedCount/totalUnique*100:>5.1f}%)  [{mergedOccurrences:>6,} occurrences]")
        
        print(f"\nMERGING DETAILS:")
        print(f"  Total words merged into others:     {mergedCount:>6}")
        print(f"  Words that received merges:         {len(mergedIntoCount):>6}")
        
        print(f"\nVERIFICATION:")
        print(f"  Sum of categories:                  {includedCount + ignoredCount + combinedCount + mergedCount:>6}")
        print(f"  Expected (total unique):            {totalUnique:>6}")
        print(f"  Match: {'✓' if includedCount + ignoredCount + combinedCount + mergedCount == totalUnique else '✗'}")
        
        print("\n" + "="*80)
        print("TOP 15 INCLUDED WORDS (by frequency)")
        print("="*80)
        print(f"{'Word':<25} {'Frequency':<12} {'Type':<20} {'Merged Into It'}")
        print("-"*80)
        for wordObj in self.includedWords[:15]:
            mergedInfo = f"({mergedIntoCount.get(wordObj.word, 0)} variants)" if wordObj.word in mergedIntoCount else ""
            wordType = wordObj.type.replace('_', ' ').title()
            print(f"{wordObj.word:<25} {wordObj.frequency:<12} {wordType:<20} {mergedInfo}")
        
        print("\n" + "="*80)
        print("TOP 10 COMBINED WORDS (hyphenated)")
        print("="*80)
        print(f"{'Word':<35} {'Frequency':<12} {'Parts'}")
        print("-"*80)
        for wordObj in self.combinedWords[:10]:
            parts = ' + '.join(wordObj.word.split('-'))
            print(f"{wordObj.word:<35} {wordObj.frequency:<12} {parts}")
        
        print("\n" + "="*80)
        print("TOP 10 MERGED WORDS")
        print("="*80)
        print(f"{'Word':<25} {'Merged Into':<25} {'Frequency':<12}")
        print("-"*80)
        for wordObj in self.mergedWords[:10]:
            print(f"{wordObj.word:<25} {wordObj.mergedWith:<25} {wordObj.frequency:<12}")
        
        print("\n" + "="*80)

    def Run(self):
        """Main processing pipeline"""
        print("="*80)
        print("RIGVEDA WORD PROCESSOR")
        print("="*80)
        
        print("\n[1/3] Loading and extracting words from hymn data...")
        self.LoadHymnData()
        
        print("\n[2/3] Processing and categorizing words...")
        self.ProcessWords(self.unfilteredWords)
        
        print("\n[3/3] Creating database...")
        self.CreateDatabase()
        print(f"      Database created at: {self.db_path}")
        
        self.PrintStatistics(self.unfilteredWords)

if __name__ == '__main__':
    processor = WordProcessor(
        json_path='/Users/nikunjgoyal/Codes/rigveda/rigveda_data.json',
        db_path='/Users/nikunjgoyal/Codes/rigveda/word_list.db'
    )
    processor.Run()
