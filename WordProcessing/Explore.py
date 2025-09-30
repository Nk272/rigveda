import json
import re
file_path = "rigveda_data.json"

with open(file_path, "r") as file:
    data = json.load(file)

print(f"Total hymns: {data['total_hymns']}")
title_map={}
skipList=set(["variousdeities", "unknown", "etc", "the", "gods", "various", "press", "post", "go", "some", "others", "new", "others-", "fathers"])

def NormalizeWord(word: str) -> str:
    """Normalize word by removing possessive and punctuation"""
    word = word.lower().strip()
    word = re.sub(r"['']s$", '', word)
    word = re.sub(r'[.,;:!?"]', '', word)
    return word

def insertintoTitleMap(deity, ref):
    if deity in skipList:
        return
    if deity not in title_map:
        title_map[deity]=[ref]
    else:
        title_map[deity].append(ref)

def get_title_map():
    for i,book in data['books'].items():
        for j,hymn in book['hymns'].items():
            title=hymn['title'].split()
            deity="UNKNOWN"

            if len(title)>2:
                deity="".join(title[2:])

            ref=f"Book {book['book_number']}, Hymn {hymn['hymn_number']}"
            deity=NormalizeWord(deity)
            if deity in skipList:
                continue
            elif deity == "brahmaṇaspati":
                deity="bṛhaspati"
                insertintoTitleMap(deity, ref)
            elif len(title)==3:
                if "-" in deity:
                    deity1=NormalizeWord(deity.split("-")[0])
                    deity2=NormalizeWord(deity.split("-")[1])
                    insertintoTitleMap(deity1, ref)
                    insertintoTitleMap(deity2, ref)
                else:
                    insertintoTitleMap(deity, ref)
            elif len(title)==4:
                deity1=NormalizeWord(title[2])
                deity2=NormalizeWord(title[3])
                insertintoTitleMap(deity1, ref)
                insertintoTitleMap(deity2, ref)
            elif len(title)==5 and NormalizeWord(title[3]) == "and":
                deity1=NormalizeWord(title[2])
                deity2=NormalizeWord(title[4])
                insertintoTitleMap(deity1, ref)
                insertintoTitleMap(deity2, ref)
            else:
                pass

    sorted_title_map=dict(sorted(title_map.items(), key=lambda x: len(x[1]), reverse=True))
    with open("title_map.json", "w", encoding='utf-8') as file:
        json.dump(sorted_title_map, file, indent=4, ensure_ascii=False)
    for k in sorted_title_map.keys():
        print(k,len(sorted_title_map[k]))




def main():
    get_title_map()
    # get_words_map()


if __name__ == "__main__":
    main()