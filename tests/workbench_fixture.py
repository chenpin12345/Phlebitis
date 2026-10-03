"""Synthetic workbench used by both API and browser regression tests. Never starts workers."""
import json
import shutil
import time
from pathlib import Path
from PIL import Image, ImageDraw
from src import common
from src.workbench import api, storage, jobs, registry, lifecycle, adapters
from src.data import dataset
from src.workbench.contracts import InferenceConfig

PROJECT=common.ROOT

def configure(root, patch, *, include_reports=False):
    home=root/'runtime/workbench'
    real_db=storage.db
    patch.setattr(storage,'db',lambda home_arg=None:real_db(home_arg or home))
    for module in (api,jobs,registry,lifecycle,adapters):
        if hasattr(module,'ROOT'): patch.setattr(module,'ROOT',root)
        if hasattr(module,'HOME'): patch.setattr(module,'HOME',home)
        if hasattr(module,'db'): patch.setattr(module,'db',lambda:real_db(home))
        if hasattr(module,'audit'): patch.setattr(module,'audit',lambda action,detail,**kwargs:storage.audit(action,detail,home=home,**kwargs))
        if hasattr(module,'read_manifest'): patch.setattr(module,'read_manifest',lambda:common.read_manifest(root))
        if hasattr(module,'inside'): patch.setattr(module,'inside',lambda path,boundary=None:common.inside(path,boundary or root))
    patch.setattr(registry,'VERSIONS',root/'models/versions');patch.setattr(registry,'REFS',root/'models/references')
    patch.setattr(jobs,'JOBS',root/'runs/workbench/jobs')
    original_review=dataset.review;original_build=dataset.build
    patch.setattr(dataset,'review',lambda ident,**kw:original_review(ident,**{'root':root,**kw}))
    patch.setattr(dataset,'build',lambda **kw:original_build(**{'root':root,**kw}))
    # Retention fixture has no expired assets; destructive endpoints aren't used by browser tests.
    patch.setattr(lifecycle,'preview_cleanup',lambda:{'assets':[],'protected':['archive','pre-existing research data','models/versions'],'note':'隔離測試，沒有到期資料。'})
    rows=[]
    specs=[('a_landscape',(160,90),1,'approved','positive'),('b_portrait',(90,160),1,'approved','negative'),('c_square',(100,100),1,'approved','positive'),('d_exif',(160,90),6,'approved','negative'),('e_positive',(150,100),1,'approved','positive'),('f_negative',(100,150),1,'approved','negative'),('p_mismatch',(160,90),6,'pending_review','positive'),('x_excluded',(130,90),1,'excluded','unknown')]
    specs.extend((f'p_{i:03}',(160,90),1,'pending_review','unknown') for i in range(34))
    for i,(ident,size,orientation,status,label) in enumerate(specs):
        base='approved' if status=='approved' else status+'/annotation' if status=='pending_review' else 'excluded/other'
        path=root/f'data/{base}/images/{ident}.jpg';path.parent.mkdir(parents=True,exist_ok=True)
        im=Image.new('RGB',size,(60+i*3,120,145));ImageDraw.Draw(im).rectangle((size[0]*.3,size[1]*.2,size[0]*.7,size[1]*.8),outline='white',width=3)
        exif=Image.Exif();exif[274]=orientation;im.save(path,exif=exif)
        lab=root/f'data/{base}/annotations/{ident}.txt';lab.parent.mkdir(parents=True,exist_ok=True);lab.write_text('0 0.5 0.5 0.4 0.6\n' if label=='positive' else '')
        annotation=''
        if ident=='p_mismatch':
            a=lab.with_suffix('.json');common.write_json(a,{'imageWidth':90,'imageHeight':160,'shapes':[{'label':'phlebitis','shape_type':'rectangle','points':[[10,20],[60,100]]}]});annotation=a.relative_to(root).as_posix()
        rows.append(dict(image_id=ident,sha256=common.sha256(path),image_path=path.relative_to(root).as_posix(),annotation_path=annotation,yolo_path=lab.relative_to(root).as_posix() if status=='approved' else '',status=status,label_state=label,candidate_group='group'+str(i//2),subject_id='subject'+str(i//2),group_verified='true' if status=='approved' else 'false',reviewer='',reason='',updated_at='',original_paths='[]'))
    common.write_manifest(rows,root)
    common.write_json(root/'configs/service.json',common.read_json(PROJECT/'configs/service.json'))
    source=root/'fixture-model';source.mkdir()
    (source/'best.pt').write_bytes(b'synthetic-weight-for-download-tests')
    common.write_json(source/'settings.json',{'names':{0:'phlebitis'},'input':{'size':[640,640]},'threshold':.5,'secret':'fixture-secret','long_text':'long-'*90})
    ident='1'*32;config={'model':'yolo11n','dataset':'fixture/fold0/dataset.yaml','device':'cpu','epochs':3,'parameters':{'lr0':.01}}
    folder=jobs.folder(ident);folder.mkdir(parents=True)
    common.write_json(folder/'request.json',{'id':ident,'kind':'train','config':config,'actor':'測試甲'})
    artifact=registry.register(source,'yolo11n',InferenceConfig().model_dump(),ident,True,{'effective':{'parameters':{'epochs':3,'lr0':.005}},'dataset':'fixture/fold0/dataset.yaml'})
    common.write_json(folder/'result.json',{'artifact':artifact['id'],'evaluation_job':'2'*32})
    common.write_json(folder/'progress.json',{'stage':'training','epoch':3,'epochs':3})
    (folder/'training').mkdir()
    (folder/'training/results.csv').write_text('epoch,train/box_loss,val/box_loss,metrics/mAP50(B)\n1,1.2,1.4,0.3\n2,0.9,nan,0.5\n3,0.7,0.8,0.6\n')
    Image.new('RGB',(240,140),'white').save(folder/'training/results.png')
    common.write_json(folder/'checkpoint_selection.json',{'epoch':3,'value':.6,'rule':'fixture recorded checkpoint event'})
    (folder/'worker.log').write_text('fixture epoch 1\nfixture epoch 2\nfixture completed\n')
    common.write_json(folder/'effective.json',{'parameters':{'epochs':3,'lr0':.005}})
    with real_db(home) as con:
        con.execute('INSERT INTO jobs(id,idem,kind,state,config,created,updated,pid,born,error) VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,ident,'train','succeeded',json.dumps(config),1000,1060,None,None,None))
        for i,(kind,model,state) in enumerate([('train','efficientnet_b0','failed'),('train','dinov2_small','succeeded'),('regression',None,'succeeded'),('future_job',None,'failed')],2):
            jid=str(i)*32;f=jobs.folder(jid);f.mkdir(parents=True);cfg={'model':model,'epochs':3} if model else {}
            con.execute('INSERT INTO jobs(id,idem,kind,state,config,created,updated,pid,born,error) VALUES(?,?,?,?,?,?,?,?,?,?)',(jid,jid,kind,state,json.dumps(cfg),1000+i,1060+i,None,None,'fixture failure' if state=='failed' else None))
            common.write_json(f/'request.json',{'id':jid,'kind':kind,'config':cfg})
            if model=='efficientnet_b0': (f/'progress.jsonl').write_text('{"epoch":1,"train_loss":0.9,"val_loss":1.1,"val_accuracy":0.5}\n{"epoch":2,"val_loss":0.8,"val_accuracy":0.7}\n')
            if kind=='regression':common.write_json(f/'result.json',{'cases':[],'note':'fixture regression test'})
        for i in range(75):
            at=1727712000+i;detail={'job':ident if i%2 else '2'*32,'_audit':{'outcome':'submitted' if i%2 else 'succeeded'}}
            con.execute('INSERT INTO audit(at,actor,action,detail) VALUES(?,?,?,?)',(at,'測試甲' if i%2 else '測試乙','enqueue' if i%2 else 'job_succeeded',json.dumps(detail)))
        con.execute('INSERT INTO audit(at,actor,action,detail) VALUES(?,?,?,?)',(1727712000,None,'legacy','{}'))
    legacy=root/'runs/historical-image-only';legacy.mkdir(parents=True);Image.new('RGB',(160,90),'white').save(legacy/'results.png')
    if include_reports:
        from src.workbench.metrics import binary_metrics
        for number,model in [(6,'yolo11n'),(7,'yolo11n'),(8,'efficientnet_b0')]:
            rid=str(number)*32;directory=root/'runs/workbench/evaluations'/rid
            samples=[{'image_id':f'history_{n:02}','truth':n%2,'prediction':n%2,'elapsed_ms':5,'status':'ok','boxes':[]} for n in range(25)]
            report={'artifact':artifact['id'] if number<8 else 'historical_classifier','artifact_hash':'synthetic','model':model,'snapshot':'fixture','fold':0,'evaluated_at':f'2026-09-{number:02}T10:00:00Z','config':InferenceConfig().model_dump(),'metrics':binary_metrics(samples),'samples':samples,'training_members_hash':'fixture-train','demo_only':True}
            common.write_json(directory/'report.json',report)
            for sample in samples[:-1]:Image.new('RGB',(240,120),'teal').save(directory/(sample['image_id']+'.jpg'))
    inbox=root/'inbox/photos/browser-batch';inbox.mkdir(parents=True)
    Image.new('RGB',(120,80),'purple').save(inbox/'new.jpg')
    (inbox/'broken.jpg').write_bytes(b'broken image')
    shutil.copytree(root/'models/versions'/artifact['id'],root/'inbox/models/browser-model')
    common.write_json(root/'inbox/models/browser-model/package.json',{'schema_version':1,'purpose':'inference','model':artifact['model'],'source':{'type':'project_artifact','id':artifact['id']},'config':artifact['config'],'files':artifact['files']})
    shutil.copytree(PROJECT/'web/dist',root/'web/dist')
    return api.create_app(testing=True),artifact

if __name__=='__main__':
    import tempfile,sys,pytest,uvicorn
    # Keep the root until the server exits, without touching the project's real runtime.
    with tempfile.TemporaryDirectory(prefix='phlebitis-ui-test-') as folder:
        with pytest.MonkeyPatch.context() as patch:
            app,_=configure(Path(folder),patch,include_reports=True)
            uvicorn.run(app,host='127.0.0.1',port=int(sys.argv[1]) if len(sys.argv)>1 else 8877,log_level='warning')
