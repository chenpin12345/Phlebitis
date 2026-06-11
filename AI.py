from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO("yolo11n.pt")

    model.train(
        data=r"C:\path\to\Phlebitis\my_data.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        device=0,
        name="trainresult"
    )