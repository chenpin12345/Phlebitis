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
        'na_reason':'N/A：分母為零或缺少必要類別；不代表 0%。'}
