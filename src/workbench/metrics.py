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

def aggregate(reports):
    if not reports: raise ValueError('No reports')
    first = reports[0]
    for report in reports:
        if report['model'] != first['model'] or report['config'] != first['config'] or report['snapshot'] != first['snapshot']:
            raise ValueError('OOF requires one recipe, inference protocol and snapshot')
        if report.get('training_protocol')!=first.get('training_protocol'):raise ValueError('OOF training strategy/seed differs across folds')
        if not report['metrics'].get('complete',True):raise ValueError('Cannot aggregate incomplete evaluation members')
    samples = [s for r in reports for s in r['samples']]
    image_ids = [s['image_id'] for s in samples]
    if len(image_ids) != len(set(image_ids)): raise ValueError('OOF member repeated across folds/seeds')
    for r in reports:
        if set(r['train_groups']) & {s['group'] for s in r['samples']}: raise ValueError('OOF group leakage')
    values = [r['metrics']['accuracy'] for r in reports if r['metrics']['accuracy'] is not None]
    expected=first.get('expected_folds')
    complete=bool(expected and len(reports)==expected and len({r.get('fold') for r in reports})==expected)
    mean=sum(values)/len(values) if values else None
    spread=(sum((v-mean)**2 for v in values)/len(values))**.5 if values else None
    return {'scope':'experiment_recipe_not_final_refit','complete_cross_validation':complete,'expected_folds':expected,'folds':len(reports),'fold_mean_accuracy':mean,'fold_std_accuracy':spread,'pooled':binary_metrics(samples,image_ids),'note':'只有完整且每個成員僅出現一次的分组切分可稱完整 OOF；不可歸屬全資料重訓模型。'}
