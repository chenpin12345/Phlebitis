"""Actual interrupted-training integration check using public Ultralytics callbacks."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,read_json,write_json,config_path
from src.paths import EVIDENCE_DIR
from src.data.dataset import latest_dataset
from src.training import runner
from src import model_api

def main():
    original=model_api.yolo_api
    previous=set((ROOT/"runs").glob("*"))
    def interrupted_api():
        YOLO=original()
        def factory(*a,**kw):
            model=YOLO(*a,**kw)
            def stop_after_save(trainer):
                if trainer.epoch==0:
                    raise InterruptedError("Deliberate integration-test interruption after first checkpoint")
            model.add_callback("on_model_save",stop_after_save)
            return model
        return factory
    model_api.yolo_api=interrupted_api
    try:
        runner.train(latest_dataset(),config=config_path("train.json"),epochs=4,demo=True)
    except InterruptedError:
        pass
    finally:
        model_api.yolo_api=original
    created=set((ROOT/"runs").glob("*"))-previous
    assert len(created)==1
    run=created.pop()
    assert (run/"weights/last.pt").exists()
    runner.train(latest_dataset(),config=config_path("train.json"),demo=True,resume=run/"weights/last.pt")
    assert read_json(run/"experiment.json")["status"]=="completed"
    rows=(run/"results.csv").read_text().splitlines()
    assert len(rows)==5,rows
    write_json(EVIDENCE_DIR/"resume-check.json",{"passed":True,"run":str(run.relative_to(ROOT)),"completed_epochs":4})
    print("Interrupted checkpoint resumed successfully to four epochs.")

if __name__=="__main__":main()
