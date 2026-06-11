from ultralytics import YOLO

if __name__ == '__main__':

    print("1. loading model")

    model = YOLO("yolo11n.pt")

    print("2. start training")

    model.train(
        data=r"C:\path\to\Phlebitis\my_data.yaml",

        #training
        epochs=120,
        imgsz=640,
        batch=4,
        device=0,

        name="train_stable_v1",

        #基本 augmentation
        degrees=5,
        translate=0.1,
        scale=0.15,

        hsv_h=0.01,
        hsv_s=0.3,
        hsv_v=0.2,

        #關閉容易破壞醫療特徵
        mosaic=0,
        mixup=0,

        fliplr=0,
        flipud=0
    )

    print("3. training finished")