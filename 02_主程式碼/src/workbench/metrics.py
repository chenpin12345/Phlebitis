from src.workbench.storage import digest

def binary_metrics(samples, expected_ids=None):
    """Never count missing/failed/unknown samples as negative or correct."""
    valid = [s for s in samples if s.get('truth') in (0,1) and s.get('prediction') in (0,1) and not s.get('error')]
    ids = [s['image_id'] for s in valid]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate evaluation image_id')
    expected = set(expected_ids if expected_ids is not None else [s['image_id'] for s in samples])
    if set(ids) - expected: raise ValueError('Unexpected evaluation members')
    missing = sorted(expected - set(ids))
    tp = sum(s['truth']==1 and s['prediction']==1 for s in valid)
    fn = sum(s['truth']==1 and s['prediction']==0 for s in valid)
    fp = sum(s['truth']==0 and s['prediction']==1 for s in valid)
    tn = sum(s['truth']==0 and s['prediction']==0 for s in valid)
    n = len(valid)
    div = lambda a,b: a/b if b else None
    recall, specificity = div(tp,tp+fn), div(tn,tn+fp)
    accuracy = div(tp+tn,n)
    answered = [s for s in valid if s.get('status') not in ('quality_rejected','needs_review')]
    return {'tp':tp,'fn':fn,'fp':fp,'tn':tn,'correct':tp+tn,'valid':n,'expected':len(expected),
        'accuracy':accuracy,'accuracy_display':('尚無可驗證準確率' if accuracy is None else f'{accuracy*100:.{0 if n<20 else 1}f}%（{tp+tn}/{n}）'),
        'sensitivity':recall,'specificity':specificity,'false_positive_rate':div(fp,fp+tn),'precision':div(tp,tp+fp),
        'f1':div(2*tp,2*tp+fp+fn),'balanced_accuracy':(recall+specificity)/2 if recall is not None and specificity is not None else None,
        'positives':tp+fn,'negatives':tn+fp,'majority_baseline':div(max(tp+fn,tn+fp),n),
        'complete':not missing,'missing_members':missing,'two_classes':bool(tp+fn and tn+fp),
        'coverage':div(len(answered),len(expected)), 'answered_accuracy':div(sum(s['truth']==s['prediction'] for s in answered),len(answered)),
        'rejected':len(valid)-len(answered),'failed':len(missing),'member_hash':digest(sorted(expected)),
        'na_reason':'N/A：分母為零或缺少必要類別；不代表 0%。','kind':'binary'}

def multiclass_metrics(samples, classes, expected_ids=None):
    """K-class metrics. Rows of the confusion matrix are truth, columns prediction.
    Missing, failed and unanswered samples are counted separately and never as correct."""
    k=len(classes)
    valid=[s for s in samples if isinstance(s.get('truth'),int) and isinstance(s.get('prediction'),int) and 0<=s['truth']<k and 0<=s['prediction']<k and not s.get('error')]
    ids=[s['image_id'] for s in valid]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate evaluation image_id')
    expected=set(expected_ids if expected_ids is not None else [s['image_id'] for s in samples])
    if set(ids)-expected:raise ValueError('Unexpected evaluation members')
    missing=sorted(expected-set(ids))
    answered=[s for s in valid if s.get('status') not in ('quality_rejected','needs_review')]
    matrix=[[sum(s['truth']==t and s['prediction']==p for s in answered) for p in range(k)] for t in range(k)]
    div=lambda a,b:a/b if b else None
    per_class={}
    for i,name in enumerate(classes):
        tp=matrix[i][i];fp=sum(matrix[t][i] for t in range(k))-tp;fn=sum(matrix[i])-tp
        precision,recall=div(tp,tp+fp),div(tp,tp+fn)
        f1=None if precision is None or recall is None else (div(2*precision*recall,precision+recall) if precision+recall else 0.0)
        per_class[name]={'precision':precision,'recall':recall,'f1':f1,'support':sum(matrix[i])}
    f1s=[v['f1'] for v in per_class.values()]
    macro_f1=sum(f1s)/k if all(f is not None for f in f1s) else None
    correct=sum(matrix[i][i] for i in range(k));n=len(answered)
    accuracy=div(correct,n)
    return {'kind':'multiclass','classes':list(classes),'confusion_matrix':matrix,'per_class':per_class,'macro_f1':macro_f1,
            'accuracy':accuracy,'accuracy_display':('尚無可驗證準確率' if accuracy is None else f'{accuracy*100:.{0 if n<20 else 1}f}%（{correct}/{n}）'),
            'support':{name:per_class[name]['support'] for name in classes},'valid':len(valid),'answered':n,'expected':len(expected),
            'undetermined':len(valid)-n,'failed':len(missing),'missing_members':missing,'complete':not missing,
            'all_classes':all(per_class[name]['support'] for name in classes),'coverage':div(n,len(expected)),
            'member_hash':digest(sorted(expected)),'na_reason':'N/A：該類別沒有樣本或沒有預測，分母為零；不代表 0%。'}
