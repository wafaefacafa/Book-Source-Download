import os

base = r"C:\Users\www20\source\repos\legado-downloader\upload\终极斗罗"
keywords = ("唐舞麟", "古月娜")

for fname in sorted(os.listdir(base)):
    if not fname.endswith('.txt'):
        continue
    path = os.path.join(base, fname)
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            if all(k in text for k in keywords):
                # split into paragraphs by blank lines or single newlines
                paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
                for p in paragraphs:
                    if all(k in p for k in keywords):
                        print(f"FOUND_IN_FILE: {fname}")
                        print("---PARAGRAPH_START---")
                        print(p)
                        print("---PARAGRAPH_END---")
                        raise SystemExit(0)
                # If no single paragraph contains both, print filename and surrounding lines
                print(f"FOUND_IN_FILE (no single paragraph): {fname}")
                # print first occurrences with some context
                for k in keywords:
                    idx = text.find(k)
                    start = max(0, idx-100)
                    end = min(len(text), idx+100)
                    print(f"---Context for {k}---")
                    print(text[start:end].replace('\n', ' '))
                raise SystemExit(0)
    except Exception as e:
        print(f"ERROR reading {fname}: {e}")

print("Not found")
