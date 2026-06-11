import json
import os
import glob

#設定路徑
# 你目前的 JSON 來源資料夾
src_json_dir = r'C:\path\to\Phlebitis\train-label'
# 你預計要存放 TXT 的 YOLO 資料集路徑
target_label_dir = r'C:\path\to\Phlebitis\YOLODataset\labels\train'

# 如果目標資料夾不存在，就建立它
if not os.path.exists(target_label_dir):
    os.makedirs(target_label_dir)

def convert():
    json_files = glob.glob(os.path.join(src_json_dir, "*.json"))
    print(f"找到 {len(json_files)} 個 JSON 檔案，開始轉換...")

    for json_path in json_files:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        img_w = data['imageWidth']
        img_h = data['imageHeight']
        file_name = os.path.splitext(os.path.basename(json_path))[0]
        
        yolo_lines = []
        for shape in data['shapes']:
            # 只處理標籤為 "靜脈炎" 且為矩形的資料
            if shape['shape_type'] == 'rectangle':
                points = shape['points']
                x1, y1 = points[0]
                x2, y2 = points[1]
                
                # 計算中心點與寬高
                x_center = (x1 + x2) / 2.0 / img_w
                y_center = (y1 + y2) / 2.0 / img_h
                w = abs(x2 - x1) / img_w
                h = abs(y2 - y1) / img_h
                
                # 類別設為 0 (phlebitis)
                yolo_lines.append(f"0 {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")
        
        # 寫入到 YOLO 資料集目錄下的 .txt
        target_path = os.path.join(target_label_dir, f"{file_name}.txt")
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(yolo_lines))

    print(f"✅ 轉換完成！TXT 檔案已存入: {target_label_dir}")

if __name__ == "__main__":
    convert()