from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1 import payments, tracking

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
app.include_router(payments.router, tags=["stripe"]) # Catch stripe routes cleanly
app.include_router(tracking.router, tags=["tracking"])

@app.get("/payment")
async def get_payment():
    return FileResponse("startbootstrap-shop-homepage-gh-pages/feza-pay.html")

@app.get("/test-page")
async def get_test_page():
    return FileResponse("test.html")

# Mount static files at root for html/css/js
app.mount("/", StaticFiles(directory=".", html=True), name="static")
