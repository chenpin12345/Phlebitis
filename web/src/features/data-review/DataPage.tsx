type Obj=Record<string,any>;
import {DataReview} from './review';
import {Heading} from '../../shared/app-ui';
export function DataPage({act}:any){return <><Heading eyebrow="DATA / REVIEW" title="先確認資料，再開始訓練。">不清楚、缺少標註或來源待查的照片，與可訓練資料分開管理。建立資料快照請前往模型與實驗 → 建立實驗。</Heading><DataReview act={act}/></>}
