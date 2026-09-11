export type FoldResult={repeat:number;fold:number;train_metrics?:Record<string,number>;validation_metrics?:Record<string,number>;labels?:number[];predictions?:number[];probabilities?:number[];train_size?:number;validation_size?:number;duration_seconds?:number;resource_measurements?:Record<string,number>};
export type BenchmarkExperimentInput={experiment_id:string;fold_results:FoldResult[]};
export type BenchmarkCreateRequest={experiments:BenchmarkExperimentInput[];primary_metric?:string;stratified?:boolean;repeats?:number;folds?:number;calibration_bins?:number;notes?:string[]};
export type BenchmarkReport={id:string;primary_metric:string;experiment_ids:string[];request:BenchmarkCreateRequest;report:Record<string,unknown>;created_at:string};
export type BenchmarkList={items:BenchmarkReport[];total:number};
