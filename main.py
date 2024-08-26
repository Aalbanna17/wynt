#import uvicorn
from fastapi import FastAPI , Request
from routers import cvextract
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#app.include_router(cvextract)
app.include_router(cvextract.router, prefix="/cv", tags=["CV wynt"])

"""
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Request headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response headers: {response.headers}")
    return response