from ultralytics import YOLO

if __name__ == '__main__':

    print("1. loading model")
   
    model = YOLO("yolo11n.pt") 

    print("2. start training")

    model.train(
        data=r"C:\path\to\Phlebitis\my_data.yaml",

        # 基礎訓練設定
        epochs=120,        
        imgsz=640,
        batch=4,
        device=0,

        name="train_clean_label_v1",

        # 幾何幾何資料增強 
        degrees=10,         # 角度
        translate=0.05,     # 邊界
        scale=0.05,         # 縮放

        # 顏色
        hsv_h=0.01,         #色相微調
        hsv_s=0.2,          #飽和度
        hsv_v=0.15,         #明暗度

        # 關鍵醫療防禦
        mosaic=0,           
        mixup=0,            

        # 翻轉增強
        fliplr=0.5,         # 允許左右翻轉
        flipud=0.0,        

        # 控制 驗證時的框選嚴格度
        conf=0.5,           # 驗證時，低於 0.5 信心度的預測框直接不顯示
        iou=0.45            # 驗證時，重疊度高於 45% 的框會被 NMS 機制濾除
    )

    print("3. training finished")