import {DataReview} from './review';
import {Heading} from '../../shared/app-ui';
export function DataPage({act}: any) {
  return (
    <>
      <Heading title="資料審查">確認每張照片的分類標籤，再用來訓練模型。</Heading>
      <DataReview act={act} />
    </>
  );
}
