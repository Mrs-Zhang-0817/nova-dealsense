import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .api.business import router as business_router
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from .api.health import router
from .core.config import settings

logging.basicConfig(level=logging.INFO)
app = FastAPI(title=settings.app_name)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_methods=["GET","POST","PUT","DELETE"], allow_headers=["*"])
app.include_router(router, prefix="/api/v1")

app.include_router(business_router, prefix="/api/v1")

@app.exception_handler(IntegrityError)
async def conflict(request, exc):
    return JSONResponse(status_code=409, content={"detail": "编号重复或记录正在被引用"})

@app.exception_handler(ValueError)
async def invalid(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    errors = [".".join(map(str,e["loc"][1:])) + " — " + e["msg"] for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "；".join(errors)})

@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    logging.getLogger(__name__).error("Request failed: %s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "服务暂时不可用"})


from .api.optimizer import router as optimizer_router
app.include_router(optimizer_router, prefix="/api/v1")

from .api.decisions import router as decisions_router
app.include_router(decisions_router, prefix="/api/v1")
