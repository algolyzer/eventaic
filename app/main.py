from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine, Base
from app.api.router import api_router
from app.utils.helpers import setup_logging
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pathlib import Path
import os

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting application...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    yield

    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/docs",  # Move docs to /api/docs
    redoc_url="/api/redoc",  # Move redoc to /api/redoc
    openapi_url="/api/openapi.json"  # Move OpenAPI spec
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS + ["http://localhost:5173"],  # Add Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )

# Add rate limiting
if settings.RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Include API router with /api/v1 prefix
app.include_router(api_router, prefix=settings.API_PREFIX)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
LANDING_PATH = PROJECT_ROOT / "eventaic-frontend" / "landing"
APP_PATH = PROJECT_ROOT / "eventaic-frontend" / "app" / "dist"

# Mount static files for landing page assets
if LANDING_PATH.exists():
    app.mount("/assets", StaticFiles(directory=str(LANDING_PATH / "assets")), name="landing_assets")

# Mount Vue app static files if built
if APP_PATH.exists():
    # Serve Vue app static files
    app.mount("/app/assets", StaticFiles(directory=str(APP_PATH / "assets")), name="app_assets")


    # Serve Vue app for /app routes
    @app.get("/app/{full_path:path}")
    async def serve_app(full_path: str):
        """Serve Vue app for all /app routes"""
        index_file = APP_PATH / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse(content="App not built. Run 'npm run build' in eventaic-frontend/app", status_code=404)
else:
    # Development mode - redirect to Vite dev server
    @app.get("/app/{full_path:path}")
    async def redirect_to_dev(full_path: str):
        """Redirect to Vite dev server in development"""
        return HTMLResponse(content=f"""
        <html>
            <head>
                <meta http-equiv="refresh" content="0; url=http://localhost:5173/app/{full_path}">
            </head>
            <body>
                <p>Redirecting to development server...</p>
                <p>If not redirected, <a href="http://localhost:5173/app/{full_path}">click here</a></p>
            </body>
        </html>
        """)


# Serve landing page at root
@app.get("/")
async def serve_landing():
    """Serve landing page at root"""
    landing_file = LANDING_PATH / "index.html"

    if landing_file.exists():
        # Read the HTML file and update paths for assets
        with open(landing_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update asset paths to be absolute
        content = content.replace('href="assets/', 'href="/assets/')
        content = content.replace('src="assets/', 'src="/assets/')

        return HTMLResponse(content=content)
    else:
        # Fallback HTML if landing page not found
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Eventaic - Event-Responsive Ad Generation</title>
            <style>
                body {
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    text-align: center;
                    padding: 20px;
                }
                h1 { font-size: 3em; margin: 0.5em 0; }
                p { font-size: 1.2em; opacity: 0.9; max-width: 600px; }
                .buttons {
                    margin-top: 2em;
                    display: flex;
                    gap: 1em;
                    flex-wrap: wrap;
                    justify-content: center;
                }
                a {
                    display: inline-block;
                    padding: 12px 30px;
                    background: white;
                    color: #667eea;
                    text-decoration: none;
                    border-radius: 30px;
                    font-weight: 600;
                    transition: transform 0.2s;
                }
                a:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
                .secondary {
                    background: transparent;
                    color: white;
                    border: 2px solid white;
                }
            </style>
        </head>
        <body>
            <h1>🚀 Eventaic</h1>
            <p>Turn real-time events into high-converting ad campaigns automatically with AI-powered generation and evaluation.</p>
            <div class="buttons">
                <a href="/app">Launch App</a>
                <a href="/api/docs" class="secondary">API Documentation</a>
            </div>
        </body>
        </html>
        """, status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG
    )
