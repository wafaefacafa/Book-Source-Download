import os
import re

def extract_specific_content():
    base_dir = r"C:\Users\www20\source\repos\legado-downloader\upload"
    output_file = r"C:\Users\www20\source\repos\legado-downloader\special_segments.txt"
    
    with open(output_file, "w", encoding="utf-8") as outfile:
        # 1. 提取终极斗罗指定章节
        zjdl_dir = os.path.join(base_dir, "终极斗罗")
        target_indices = ["1679", "1680", "1681", "1682", "1683", "1792", "1793"]
        
        if os.path.exists(zjdl_dir):
            outfile.write("========== 终极斗罗 指定内容 ==========\n\n")
            files = sorted(os.listdir(zjdl_dir))
            for f in files:
                # 检查文件名开头是否包含目标序号 (例如 "1679_")
                if any(f.startswith(idx) for idx in target_indices):
                    file_path = os.path.join(zjdl_dir, f)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
                            content = infile.read()
                            outfile.write(f"--- 章节: {f} ---\n")
                            outfile.write(content.strip() + "\n\n")
                    except Exception as e:
                        outfile.write(f"Error reading {f}: {e}\n")

        # 2. 提取龙王传说求婚剧情
        lwcs_dir = os.path.join(base_dir, "龙王传说_分割")
        if os.path.exists(lwcs_dir):
            outfile.write("\n========== 龙王传说 求婚相关段落 ==========\n\n")
            files = sorted(os.listdir(lwcs_dir))
            for f in files:
                if f.endswith(".txt"):
                    file_path = os.path.join(lwcs_dir, f)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
                            content = infile.read()
                            # 求婚通常跨越多行，按段落分割检索
                            paragraphs = content.split('\n')
                            current_scene = []
                            is_collecting = False
                            
                            for para in paragraphs:
                                text = para.strip()
                                if not text: continue
                                
                                # 检索求婚、嫁给我、娶你、戒指等关键词
                                if any(kw in text for kw in ["求婚", "嫁给我", "娶你", "单膝下跪", "戒指"]):
                                    outfile.write(f"--- 来源: {f} ---\n")
                                    outfile.write(text + "\n\n")
                                    
                    except Exception as e:
                        outfile.write(f"Error reading {f}: {e}\n")

    print(f"提取完成，结果保存在: {output_file}")

if __name__ == "__main__":
    extract_specific_content()
