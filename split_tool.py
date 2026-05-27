import os

def split_file(input_file, chunk_size_mb, output_dir):
    chunk_size = chunk_size_mb * 1024 * 1024
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    file_name = os.path.basename(input_file)
    base_name, extension = os.path.splitext(file_name)
    
    with open(input_file, 'rb') as f:
        chunk_num = 1
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            output_file = os.path.join(output_dir, f"{base_name}_part{chunk_num}{extension}")
            with open(output_file, 'wb') as chunk_file:
                chunk_file.write(chunk)
            
            print(f"Created: {output_file}")
            chunk_num += 1

if __name__ == "__main__":
    input_txt = r"C:\Users\www20\source\repos\legado-downloader\斗罗大陆3龙王传说.txt"
    output_folder = r"C:\Users\www20\source\repos\legado-downloader\龙王传说_分割"
    split_file(input_txt, 10, output_folder)
