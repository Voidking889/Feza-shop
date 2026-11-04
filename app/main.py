from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.api.v1 import payments, tracking
from app.api.v1 import orders
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.models.purchase import Customer, PurchaseItem, PurchaseOrder
    from app.models.transaction import Transaction

    database_url = make_url(settings.DATABASE_URL)
    if database_url.get_backend_name() == "sqlite" and database_url.database not in (None, ":memory:"):
        Path(database_url.database).parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield

BASE_DIR = Path(__file__).resolve().parents[1]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def protect_private_files(request, call_next):
    if any(part.startswith(".") for part in request.url.path.strip("/").split("/")):
        return Response(status_code=404)
    return await call_next(request)

# Include Routers
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
app.include_router(payments.router, tags=["stripe"]) # Catch stripe routes cleanly
app.include_router(tracking.router, tags=["tracking"])
app.include_router(orders.router, prefix="/api/v1", tags=["orders"])

@app.get("/payment")
async def get_payment():
    return FileResponse(BASE_DIR / "feza-pay.html")

@app.get("/test-page")
async def get_test_page():
    return FileResponse(BASE_DIR / "test.html")

# Mount static files at root for html/css/js
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")
