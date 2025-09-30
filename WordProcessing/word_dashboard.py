import sqlite3
from flask import Flask, render_template, jsonify, request
from difflib import SequenceMatcher
import threading

app = Flask(__name__)

includedWords = {}
ignoredWords = set()
combinedWords = {}
dbLock = threading.Lock()

DB_PATH = 'word_list.db'

def GetDbConnection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def LoadFromDatabase():
    global includedWords, ignoredWords, combinedWords
    
    conn = GetDbConnection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT word, frequency, merged_with, word_type FROM included_words')
    for word, freq, mergedWith, wordType in cursor.fetchall():
        mergedList = mergedWith.split(',') if mergedWith else []
        includedWords[word] = {
            'frequency': freq,
            'merged_with': mergedList,
            'type': wordType
        }
    
    cursor.execute('SELECT word FROM ignored_words')
    ignoredWords = {word for (word,) in cursor.fetchall()}
    
    cursor.execute('SELECT word, frequency, parts FROM combined_words')
    for word, freq, parts in cursor.fetchall():
        combinedWords[word] = {
            'frequency': freq,
            'parts': parts.split(',')
        }
    
    conn.close()
    print(f"Loaded {len(includedWords)} included words, {len(ignoredWords)} ignored words, {len(combinedWords)} combined words")

def SaveToDatabase():
    with dbLock:
        conn = GetDbConnection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM included_words')
        cursor.execute('DELETE FROM ignored_words')
        cursor.execute('DELETE FROM combined_words')
        
        for word, data in includedWords.items():
            mergedWith = ','.join(data['merged_with'])
            cursor.execute(
                'INSERT INTO included_words VALUES (?, ?, ?, ?)',
                (word, data['frequency'], mergedWith, data['type'])
            )
        
        for word in ignoredWords:
            cursor.execute('INSERT INTO ignored_words VALUES (?)', (word,))
        
        for word, data in combinedWords.items():
            parts = ','.join(data['parts'])
            cursor.execute(
                'INSERT INTO combined_words VALUES (?, ?, ?)',
                (word, data['frequency'], parts)
            )
        
        conn.commit()
        conn.close()

def CalculateSimilarity(word1, word2):
    return SequenceMatcher(None, word1.lower(), word2.lower()).ratio()

@app.route('/')
def Index():
    return render_template('dashboard.html')

@app.route('/api/words')
def GetWords():
    allWords = []
    
    for word, data in includedWords.items():
        allWords.append({
            'word': word,
            'frequency': data['frequency'],
            'type': data['type'],
            'merged_count': len(data['merged_with'])
        })
    
    allWords.sort(key=lambda x: x['frequency'], reverse=True)
    
    stats = {
        'included': len(includedWords),
        'ignored': len(ignoredWords),
        'combined': len(combinedWords),
        'total': len(includedWords) + len(ignoredWords) + len(combinedWords)
    }
    
    return jsonify({
        'words': allWords,
        'stats': stats
    })

@app.route('/api/combined-words')
def GetCombinedWords():
    words = []
    for word, data in combinedWords.items():
        words.append({
            'word': word,
            'frequency': data['frequency'],
            'parts': data['parts']
        })
    
    words.sort(key=lambda x: x['frequency'], reverse=True)
    return jsonify({'words': words})

@app.route('/api/ignored-words')
def GetIgnoredWords():
    return jsonify({'words': sorted(list(ignoredWords))})

@app.route('/api/move-to-ignored', methods=['POST'])
def MoveToIgnored():
    word = request.json.get('word')
    
    if word in includedWords:
        ignoredWords.add(word)
        del includedWords[word]
        
        threading.Thread(target=SaveToDatabase, daemon=True).start()
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Word not found'})

@app.route('/api/move-to-included', methods=['POST'])
def MoveToIncluded():
    word = request.json.get('word')
    
    if word in ignoredWords:
        ignoredWords.remove(word)
        includedWords[word] = {
            'frequency': 1,
            'merged_with': [],
            'type': 'standard'
        }
        
        threading.Thread(target=SaveToDatabase, daemon=True).start()
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Word not found'})

@app.route('/api/merge', methods=['POST'])
def MergeWord():
    sourceWord = request.json.get('word')
    targetWord = request.json.get('targetWord')
    
    if sourceWord not in includedWords or targetWord not in includedWords:
        return jsonify({'status': 'error', 'message': 'Words not found'})
    
    sourceData = includedWords[sourceWord]
    targetData = includedWords[targetWord]
    
    targetData['frequency'] += sourceData['frequency']
    targetData['merged_with'].append(sourceWord)
    targetData['merged_with'].extend(sourceData['merged_with'])
    
    del includedWords[sourceWord]
    
    threading.Thread(target=SaveToDatabase, daemon=True).start()
    
    return jsonify({'status': 'success'})

@app.route('/api/similar-words', methods=['POST'])
def GetSimilarWords():
    word = request.json.get('word')
    
    similarWords = []
    for otherWord, data in includedWords.items():
        if otherWord != word:
            similarity = CalculateSimilarity(word, otherWord)
            if similarity > 0.6:
                similarWords.append({
                    'word': otherWord,
                    'frequency': data['frequency'],
                    'similarity': round(similarity * 100, 2),
                    'type': data['type']
                })
    
    similarWords.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify({'similarWords': similarWords[:20]})

@app.route('/api/word-details', methods=['POST'])
def GetWordDetails():
    word = request.json.get('word')
    
    if word in includedWords:
        data = includedWords[word]
        return jsonify({
            'status': 'success',
            'word': word,
            'frequency': data['frequency'],
            'type': data['type'],
            'merged_with': data['merged_with']
        })
    
    return jsonify({'status': 'error', 'message': 'Word not found'})

if __name__ == '__main__':
    print("="*80)
    print("RIGVEDA WORD DASHBOARD")
    print("="*80)
    
    print("\nLoading word list from database...")
    try:
        LoadFromDatabase()
        
        print("\nStatistics:")
        print(f"  Included words:  {len(includedWords):>6}")
        print(f"  Ignored words:   {len(ignoredWords):>6}")
        print(f"  Combined words:  {len(combinedWords):>6}")
        print(f"  {'─'*40}")
        print(f"  Total:           {len(includedWords) + len(ignoredWords) + len(combinedWords):>6}")
        
        print("\n" + "="*80)
        print("Starting dashboard on http://localhost:5001")
        print("="*80)
        app.run(debug=True, port=5001)
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nPlease run 'python word_processor.py' first to generate the database.")