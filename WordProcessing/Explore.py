# url ="https://sacred-texts.com/hin/rigveda/index.htm"
import json

# Load stopwords from file
# def load_stopwords():
#     with open("stopwords.txt", "r", encoding='utf-8') as file:
#         stopwords_list = [line.strip() for line in file if line.strip()]
#     return set(stopwords_list)

# stop_words = load_stopwords()
# print(f"Filtering out {len(stop_words)} stopwords from custom file: {', '.join(sorted(list(stop_words))[:10])}...")

file_path = "rigveda_data.json"


with open(file_path, "r") as file:
    data = json.load(file)

# print(data.keys())
print(data['total_hymns'])
hm=0
title_map={}
titles=[]
words=set()
import re
def get_title_map():
    for i,book in data['books'].items():
        for j,hymn in book['hymns'].items():
            title=hymn['title'].split()
            text=hymn['text']
            words.update(re.findall(r'\b[\w-]+\b', text))
            # for word in text:
            #     words.add(word.lower().strip())
            # words.update(text.split())
    print(len(words))
            # if len(title)<3:
            #     deity="UNKNOWN"
            # elif len(title)==3:
            #     deity=title[2].strip(".")
            # else:
            #     deity="".join(title[2:])

            # ref=f"Book {book['book_number']}, Hymn {hymn['hymn_number']}"

            # if deity not in title_map:
            #     title_map[deity]=[ref]
            # else:
            #     title_map[deity].append(ref)

    # sorted_title_map=dict(sorted(title_map.items(), key=lambda x: len(x[1]), reverse=True))
    # for k in sorted_title_map.keys():
    #     print(k,len(sorted_title_map[k]))

def get_words_map():
    words_map={}
    for i,book in data['books'].items():
        for j,hymn in book['hymns'].items():
            text=hymn['text']
            words=text.split()
            ref=f"Book {book['book_number']}, Hymn {hymn['hymn_number']}"
            for word in words:
                wordl=word.lower().strip(".,!?\"'()")
                # Filter out stopwords and short words
                # if wordl not in stop_words and len(wordl) > 2:
                if wordl not in words_map:
                    words_map[wordl]=[ref]
                else:
                    words_map[wordl].append(ref)
    sorted_words_map=dict(sorted(words_map.items(), key=lambda x: len(x[1]), reverse=True))
    with open("words_map.json", "w", encoding='utf-8') as file:
        json.dump(sorted_words_map, file, indent=4, ensure_ascii=False)
    with open("words_map.txt", "w", encoding='utf-8') as file:
        for k in sorted_words_map.keys():
            file.write(f"{k} - {len(sorted_words_map[k])}\n")
    return sorted_words_map
get_title_map()
# wm=
# print("\nTop 20 most frequent meaningful words (stopwords filtered):")
# for i, k in enumerate(wm.keys()):
#     if i < 50:
#         print(f"{i+1:2d}. {k:<15} - {len(wm[k]):4d} occurrences")
#     else:
#         break

# with open("title_map.json", "w", encoding='utf-8') as file:
#     json.dump(sorted_title_map, file, indent=4, ensure_ascii=False)