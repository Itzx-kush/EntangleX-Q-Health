import unittest
import pandas as pd
from app.preprocessing.outliers import OutlierPolicy
class OutlierPolicyTests(unittest.TestCase):
    def test_iqr_bounds_are_fitted_and_clip_uses_them(self):
        train=pd.DataFrame({"x":[1,2,2,3,100]});policy=OutlierPolicy("iqr",1.5).fit(train);result=policy.clip(pd.DataFrame({"x":[-50,500]}));low,high=policy.bounds["x"];self.assertEqual(result.iloc[0,0],low);self.assertEqual(result.iloc[1,0],high)
    def test_remove_mask_preserves_missing_for_imputation(self):
        frame=pd.DataFrame({"x":[1,2,None,100]});policy=OutlierPolicy("iqr",1.0).fit(frame);mask=policy.inlier_mask(frame);self.assertTrue(mask.iloc[2])
if __name__=="__main__":unittest.main()
