import json
import re
import sqlite3
from collections import Counter
from flask import Flask, render_template, jsonify, request
from difflib import SequenceMatcher
import threading

app = Flask(__name__)

wordFrequencies = {}
mergedWords = {}
removedWords = set()
dbLock = threading.Lock()

DB_PATH = 'word_curation.db'

def GetDbConnection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def InitializeDatabase():
    conn = GetDbConnection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS merged_words (
            word TEXT PRIMARY KEY,
            merged_into TEXT NOT NULL,
            original_frequency INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS removed_words (
            word TEXT PRIMARY KEY
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_merged_into ON merged_words(merged_into)')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

def LoadFromDatabase():
    global mergedWords, removedWords
    
    conn = GetDbConnection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT word, merged_into, original_frequency FROM merged_words')
    for word, mergedInto, origFreq in cursor.fetchall():
        if mergedInto not in mergedWords:
            mergedWords[mergedInto] = {'frequency': 0, 'merged_from': []}
        mergedWords[mergedInto]['frequency'] += origFreq
        mergedWords[mergedInto]['merged_from'].append(word)
    
    cursor.execute('SELECT word FROM removed_words')
    removedWords = {word for (word,) in cursor.fetchall()}
    
    conn.close()
    print(f"Loaded {len(mergedWords)} merged word groups and {len(removedWords)} removed words from database")

def LoadRigvedaData():
    with open('rigveda_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def ExtractWords(text):
    words = text.split()
    words = [word.lower().strip(".,!?\"'()") for word in words]
    return words

def CalculateWordFrequencies():
    global wordFrequencies
    data = LoadRigvedaData()
    allWords = []
    
    for bookNum, bookData in data['books'].items():
        for hymnNum, hymnData in bookData['hymns'].items():
            words = ExtractWords(hymnData['text'])
            allWords.extend(words)
    
    wordFrequencies = dict(Counter(allWords))
    return wordFrequencies

def CalculateSimilarity(word1, word2):
    return SequenceMatcher(None, word1.lower(), word2.lower()).ratio()

@app.route('/')
def Index():
    return render_template('dashboard.html')

@app.route('/api/words')
def GetWords():
    activeWords = {}
    
    for word, freq in wordFrequencies.items():
        if word not in removedWords:
            if word in mergedWords:
                activeWords[word] = mergedWords[word]['frequency']
            else:
                activeWords[word] = freq
    
    sortedWords = sorted(activeWords.items(), key=lambda x: x[1], reverse=True)
    
    return jsonify({
        'words': [{'word': w, 'frequency': f} for w, f in sortedWords]
    })

@app.route('/api/remove', methods=['POST'])
def RemoveWord():
    word = request.json.get('word')
    removedWords.add(word)
    
    def SaveToDb():
        with dbLock:
            conn = GetDbConnection()
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO removed_words (word) VALUES (?)', (word,))
            conn.commit()
            conn.close()
    
    threading.Thread(target=SaveToDb, daemon=True).start()
    
    return jsonify({'status': 'success'})

@app.route('/api/merge', methods=['POST'])
def MergeWord():
    word = request.json.get('word')
    targetWord = request.json.get('targetWord')
    
    wordFreq = wordFrequencies.get(word, 0)
    
    if targetWord not in mergedWords:
        mergedWords[targetWord] = {
            'frequency': wordFrequencies.get(targetWord, 0),
            'merged_from': []
        }
    
    mergedWords[targetWord]['frequency'] += wordFreq
    mergedWords[targetWord]['merged_from'].append(word)
    removedWords.add(word)
    
    def SaveToDb():
        with dbLock:
            conn = GetDbConnection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO merged_words (word, merged_into, original_frequency) 
                VALUES (?, ?, ?)
            ''', (word, targetWord, wordFreq))
            cursor.execute('INSERT OR IGNORE INTO removed_words (word) VALUES (?)', (word,))
            conn.commit()
            conn.close()
    
    threading.Thread(target=SaveToDb, daemon=True).start()
    
    return jsonify({'status': 'success'})

@app.route('/api/similar-words', methods=['POST'])
def GetSimilarWords():
    word = request.json.get('word')
    
    similarWords = []
    for otherWord, freq in wordFrequencies.items():
        if otherWord != word and otherWord not in removedWords:
            similarity = CalculateSimilarity(word, otherWord)
            if similarity > 0.3:
                displayFreq = mergedWords[otherWord]['frequency'] if otherWord in mergedWords else freq
                similarWords.append({
                    'word': otherWord,
                    'frequency': displayFreq,
                    'similarity': round(similarity * 100, 2)
                })
    
    similarWords.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify({'similarWords': similarWords[:50]})

@app.route('/api/reset', methods=['POST'])
def ResetData():
    global mergedWords, removedWords
    mergedWords = {}
    removedWords = set()
    
    with dbLock:
        conn = GetDbConnection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM merged_words')
        cursor.execute('DELETE FROM removed_words')
        conn.commit()
        conn.close()
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    print("Initializing database...")
    InitializeDatabase()
    
    print("Loading Rigveda data and calculating word frequencies...")
    CalculateWordFrequencies()
    print(f"Total unique words: {len(wordFrequencies)}")
    
    print("Loading previous curation from database...")
    LoadFromDatabase()
    
    print("\nStarting dashboard on http://localhost:5001")
    app.run(debug=True, port=5001)
