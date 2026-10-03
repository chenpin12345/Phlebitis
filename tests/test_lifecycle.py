import io,json,time
import pytest
from PIL import Image
from src.common import read_json,write_json
from test_data import dataset

@pytest.fixture
def isolated(dataset,monkeypatch):
    from src import common
    from src.workbench import lifecycle,research,storage
    root=dataset;home=root/'runtime/workbench'
    (root/'configs').mkdir()
    write_json(root/'configs/service.json',{'max_image_bytes':10485760,'max_image_pixels':25000000,'allowed_formats':['JPEG','PNG','WEBP']})
    for module in (lifecycle,research):
        monkeypatch.setattr(module,'ROOT',root)
        monkeypatch.setattr(module,'db',lambda:storage.db(home))
        monkeypatch.setattr(module,'audit',lambda *a,**k:None)
        monkeypatch.setattr(module,'read_manifest',lambda:common.read_manifest(root))
        monkeypatch.setattr(module,'write_manifest',lambda rows:common.write_manifest(rows,root))
    monkeypatch.setattr(lifecycle,'HOME',home)
    return root,home,lifecycle,research

def raw(color='blue'):
    image=Image.new('RGB',(120,100),color);buf=io.BytesIO();image.save(buf,'JPEG');return buf.getvalue()

def test_upload_authorization_and_expiry(isolated):
    root,home,life,research=isolated
    with pytest.raises(ValueError,match='授權'):life.upload(raw(),research=True)
    temp=life.upload(raw());reserved=life.upload(raw('green'),research=True,authorization='synthetic test consent',purpose='automated test')
    assert 3590<temp['expires']-time.time()<=3600
    assert 29.9*86400<reserved['expires']-time.time()<=30*86400
    assert life.asset_path(temp['id']).is_file()
    assert not life.preview_cleanup()['assets']

def test_research_promote_review_snapshot_and_withdraw(isolated):
    from src.workbench.storage import db
    from src.data.dataset import review,build,validate_split
    root,home,life,research=isolated
    asset=life.upload(raw(),research=True,authorization='synthetic test',purpose='fixture')
    case={'id':'a'*32,'asset':asset['id'],'state':'confirmed','label':'negative','reviewer':'tester','notes':'synthetic','boxes':[]}
    with db(home) as con:con.execute('INSERT INTO cases(id,revision,data) VALUES(?,?,?)',(case['id'],1,json.dumps(case)))
    row=research.promote(case['id'],subject_id='new-subject')
    review(row['image_id'],status='approved',label='negative',reviewer='tester',reason='synthetic',subject_id='new-subject',root=root)
    info=build(root=root)
    with db(home) as con:con.execute('UPDATE assets SET expires=? WHERE id=?',(time.time()-1,asset['id']))
    preview=life.preview_cleanup()
    assert info['version'] in preview['assets'][0]['impact']['snapshots']
    result=life.cleanup([asset['id']]);assert result['deleted']==[asset['id']]
    assert all(r['image_id']!=row['image_id'] for r in life.read_manifest())
    with pytest.raises(ValueError,match='withdrawn'):validate_split(root/info['folds'][0]['dataset'],root)
    with db(home) as con:assert json.loads(con.execute('SELECT data FROM cases').fetchone()[0])['state']=='withdrawn'
    assert len(life.read_manifest())==6  # pre-existing records remain intact

def test_import_failure_rolls_back_and_independent_duplicate_rejected(isolated,monkeypatch):
    from src.workbench.storage import db
    root,home,life,research=isolated
    asset=life.upload(raw(),research=True,authorization='test consent',purpose='test')
    case={'id':'b'*32,'asset':asset['id'],'state':'confirmed','label':'negative','reviewer':'tester','boxes':[]}
    with db(home) as con:con.execute('INSERT INTO cases(id,revision,data) VALUES(?,?,?)',(case['id'],1,json.dumps(case)))
    original=research.write_manifest
    def fail(rows):raise OSError('disk failure')
    monkeypatch.setattr(research,'write_manifest',fail)
    with pytest.raises(OSError):research.promote(case['id'])
    assert len(life.read_manifest())==6
    assert not list((root/'data/pending_review').rglob('*.jpg'))
    monkeypatch.setattr(research,'write_manifest',original)
    research.promote(case['id'],independent=True,subject_id='external')
    with pytest.raises(ValueError,match='reserved'):research.promote(case['id'])

def test_cleanup_refuses_live_assets(isolated):
    _,_,life,_=isolated
    asset=life.upload(raw())
    with pytest.raises(ValueError,match='preview'):life.cleanup([asset['id']])
    assert life.asset_path(asset['id']).exists()

def test_busy_withdraw_has_no_partial_expiry(isolated):
    from src.lock import OperationLock
    _,_,life,_=isolated
    asset=life.upload(raw(),research=True,authorization='synthetic consent',purpose='test')
    with OperationLock():
        with pytest.raises(RuntimeError):life.withdraw(asset['id'])
    assert life.asset_path(asset['id']).exists()
    assert not life.preview_cleanup()['assets']
    assert life.withdraw(asset['id'])['deleted']==[asset['id']]
