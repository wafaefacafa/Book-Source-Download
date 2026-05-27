import os

def extract_segments():
    source_dirs = [
        r'C:\Users\www20\source\repos\legado-downloader\upload\龙王传说_分割',
        r'C:\Users\www20\source\repos\legado-downloader\upload\终极斗罗'
    ]
    output_path = r'C:\Users\www20\source\repos\legado-downloader\extracted_romance.txt'
    
    keywords = ["唐舞麟", "古月娜", "婚礼"]
    
    extracted_count = 0
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for s_dir in source_dirs:
            if not os.path.exists(s_dir):
                print(f"Directory not found: {s_dir}")
                continue
                
            print(f"Processing directory: {s_dir}")
            # Sort files to maintain order (especially for split files and chapters)
            files = sorted(os.listdir(s_dir))
            
            for filename in files:
                if not filename.endswith('.txt'):
                    continue
                
                file_path = os.path.join(s_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        # Split by empty lines or double newlines to get paragraphs
                        paragraphs = content.split('\n')
                        
                        for para in paragraphs:
                            para = para.strip()
                            if not para:
                                continue
                            
                            # Matching logic:
                            # 1. Contains '婚礼'
                            # 2. OR contains BOTH '唐舞麟' AND '古月娜' (more precise for romance)
                            # To be safe and follow the strict keywords request, we'll check if keywords are present.
                            match = False
                            if "婚礼" in para:
                                match = True
                            elif "唐舞麟" in para and "古月娜" in para:
                                match = True
                            
                            if match:
                                outfile.write(f"--- Source: {filename} ---\n")
                                outfile.write(para + "\n\n")
                                extracted_count += 1
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    print(f"Extraction complete. Total paragraphs extracted: {extracted_count}")
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    extract_segments()
