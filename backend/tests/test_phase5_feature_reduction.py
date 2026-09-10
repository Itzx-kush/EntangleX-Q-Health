from __future__ import annotations
import importlib.util,unittest
import numpy as np
SKLEARN_AVAILABLE=importlib.util.find_spec("sklearn") is not None
@unittest.skipUnless(SKLEARN_AVAILABLE,"scikit-learn not installed")
class FeatureReductionTests(unittest.TestCase):
 def setUp(self):
  from app.preprocessing.feature_reduction import reduce_features
  self.reduce=reduce_features;self.X=np.array([[i,i%2,i*2,1] for i in range(20)],dtype=float);self.test=np.array([[21,1,42,1],[22,0,44,1]],dtype=float);self.y=np.array([i%2 for i in range(20)]);self.names=["a","b","c","constant"]
 def test_variance_filter_fits_training_only(self):
  result=self.reduce(self.X,self.test,self.y,self.names,"variance",3,0,"none",2,42);self.assertNotIn("constant",result.selected_feature_names)
 def test_anova_selects_requested_count(self):self.assertEqual(self.reduce(self.X,self.test,self.y,self.names,"anova",2,0,"none",2,42).train.shape[1],2)
 def test_mutual_information_is_deterministic(self):
  a=self.reduce(self.X,self.test,self.y,self.names,"mutual_info",2,0,"none",2,42);b=self.reduce(self.X,self.test,self.y,self.names,"mutual_info",2,0,"none",2,42);self.assertEqual(a.selected_feature_names,b.selected_feature_names)
 def test_pca_reports_real_explained_variance(self):
  result=self.reduce(self.X,self.test,self.y,self.names,"variance",3,0,"pca",2,42);self.assertEqual(result.output_feature_names,["PC1","PC2"]);self.assertLessEqual(sum(result.explained_variance_ratio),1.0000001)
if __name__=="__main__":unittest.main()
