import cv2
from ultralytics import YOLO

#載入訓練好的模型
model = YOLO("runs/detect/train_stable_v1-3/weights/best.pt")

#要測試的圖片
image_path = r"C:\path\to\Phlebitis\作業\20260104_BED04_LL_2_2.jpg"

#進行預測
results = model(image_path, verbose=False)

#判斷是否有偵測到物件
detected = False
annotated_img = None

for result in results:
    # 如果有偵測到任何框就讓偵測設為True
    if result.boxes is not None and len(result.boxes) > 0:
        detected = True
       
        annotated_img = result.plot()
        break  

#輸出結果 
if detected:
    print("YES")
    # 如果有偵測到就顯示出來
    if annotated_img is not None:
        cv2.imshow("Detection - YES", annotated_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
else:
    print("NO")
    # 看原圖
    img = cv2.imread(image_path)
    cv2.imshow("No Detection - NO", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()