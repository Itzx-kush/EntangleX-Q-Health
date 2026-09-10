from __future__ import annotations
import importlib.util,unittest
import numpy as np
IMBLEARN_AVAILABLE=importlib.util.find_spec("imblearn") is not None
@unittest.skipUnless(IMBLEARN_AVAILABLE,"imbalanced-learn not installed")
class ResamplingTests(unittest.TestCase):
 def setUp(self):
  from app.preprocessing.resampling import apply_resampling
  self.apply=apply_resampling;self.X=np.arange(20,dtype=float).reshape(10,2);self.y=np.array([0]*8+[1]*2)
 def test_none_preserves_training_rows(self):self.assertEqual(self.apply(self.X,self.y,"none",42,1).distribution_after,{"0":8,"1":2})
 def test_random_over_balances_training_only(self):
  result=self.apply(self.X,self.y,"random_over",42,1);self.assertEqual(result.distribution_after,{"0":8,"1":8});self.assertEqual(result.rows_added,6)
 def test_random_under_balances_training_only(self):
  result=self.apply(self.X,self.y,"random_under",42,1);self.assertEqual(result.distribution_after,{"0":2,"1":2});self.assertEqual(result.rows_removed,6)
 def test_smote_balances_with_valid_neighbors(self):self.assertEqual(self.apply(self.X,self.y,"smote",42,1).distribution_after,{"0":8,"1":8})
if __name__=="__main__":unittest.main()
