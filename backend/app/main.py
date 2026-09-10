from __future__ import annotations
import logging
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.datasets import router as dataset_router
from app.api.health import router as health_router
from app.api.models import router as model_router
from app.api.preprocessing import router as preprocessing_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.data.errors import DatasetError
from app.ml.errors import ModelTrainingError
from app.preprocessing.errors import PreprocessingError
configure_logging();logger=logging.getLogger(__name__)
def create_app()->FastAPI:
 app=FastAPI(title=settings.app_name,version=settings.app_version,description='Research and decision-support platform for reproducible hybrid quantum-classical biomedical ML.')
 app.add_middleware(CORSMiddleware,allow_origins=list(settings.cors_origins),allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['*'])
 app.include_router(health_router);app.include_router(health_router,prefix='/api/v1');app.include_router(dataset_router);app.include_router(preprocessing_router);app.include_router(model_router)
 @app.exception_handler(DatasetError)
 async def dataset_error(_:Request,exc:DatasetError)->JSONResponse:return JSONResponse(status_code=exc.status_code,content={'error':exc.code,'message':exc.message,'details':exc.details})
 @app.exception_handler(PreprocessingError)
 async def preprocessing_error(_:Request,exc:PreprocessingError)->JSONResponse:return JSONResponse(status_code=exc.status_code,content={'error':exc.code,'message':exc.message,'details':exc.details})
 @app.exception_handler(ModelTrainingError)
 async def model_error(_:Request,exc:ModelTrainingError)->JSONResponse:return JSONResponse(status_code=exc.status_code,content={'error':exc.code,'message':exc.message,'details':exc.details})
 @app.exception_handler(Exception)
 async def unhandled_error(_:Request,exc:Exception)->JSONResponse:logger.exception('Unhandled API error');return JSONResponse(status_code=500,content={'error':'INTERNAL_ERROR','message':'The request could not be completed.','details':None})
 return app
app=create_app()
