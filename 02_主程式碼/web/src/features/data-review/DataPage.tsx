import {DataReview} from './review';
import {Heading} from '../../shared/app-ui';
export function DataPage({act}:any){return <><Heading title="資料審查">YOLO 框選區與其他模型分類區分開處理，在一區的操作不會改變另一區。</Heading><DataReview act={act}/></>}
