from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
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
import time
import traceback

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
    logger.info("🚀 Starting Eventaic application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Validate production config
    if settings.is_production:
        warnings = settings.validate_production_config()
        if warnings:
            logger.warning("⚠️ Production configuration warnings:")
            for warning in warnings:
                logger.warning(f"  {warning}")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise

    yield

    logger.info("👋 Shutting down Eventaic application...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,  # Disable in production
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None
)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    # Add security headers
    if settings.ENABLE_SECURITY_HEADERS:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if settings.is_production:
            # Strict Transport Security (HTTPS only)
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

            # Content Security Policy
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.dify.ai;"
            )

    # Add request ID for tracking
    request_id = request.headers.get("X-Request-ID", str(time.time()))
    response.headers["X-Request-ID"] = request_id

    # Log request duration
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log slow requests
    if process_time > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s"
        )

    return response


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"]
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted host middleware (production only)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with your domain
    )

# Rate limiting
if settings.RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code}: {request.method} {request.url.path} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {request.method} {request.url.path} - {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "body": exc.body if hasattr(exc, 'body') else None
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    error_id = str(time.time())
    logger.error(
        f"Unhandled exception [{error_id}]: {request.method} {request.url.path}",
        exc_info=True
    )

    # Don't expose internal errors in production
    if settings.is_production:
        detail = "Internal server error"
    else:
        detail = f"{type(exc).__name__}: {str(exc)}"

    return JSONResponse(
        status_code=500,
        content={
            "detail": detail,
            "error_id": error_id if settings.DEBUG else None
        }
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": time.time()
    }


@app.get("/health/detailed", tags=["System"])
async def detailed_health_check():
    """Detailed health check with all services"""
    health_status = {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "services": {}
    }

    # Check database
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        start = time.time()
        db.execute("SELECT 1")
        db.close()
        health_status["services"]["database"] = {
            "status": "healthy",
            "response_time": time.time() - start
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check Redis (if enabled)
    if settings.REDIS_ENABLED and settings.REDIS_URL:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            start = time.time()
            r.ping()
            health_status["services"]["redis"] = {
                "status": "healthy",
                "response_time": time.time() - start
            }
        except Exception as e:
            health_status["services"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }

    # Overall status
    all_healthy = all(
        service.get("status") == "healthy"
        for service in health_status["services"].values()
    )
    health_status["status"] = "healthy" if all_healthy else "degraded"

    return health_status


# Favicon route
@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    PROJECT_ROOT = Path(__file__).parent.parent
    favicon_path = PROJECT_ROOT / "eventaic-frontend" / "landing" / "assets" / "favicon.ico"

    if not favicon_path.exists():
        # Return simple SVG favicon
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <defs>
                <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
                    <stop stop-color="#7c5cff"/>
                    <stop stop-color="#00d4ff" offset="1"/>
                </linearGradient>
            </defs>
            <rect rx="14" width="64" height="64" fill="url(#g)"/>
            <text x="50%" y="58%" text-anchor="middle" font-size="34" font-family="Arial" fill="white">E</text>
        </svg>"""
        return HTMLResponse(content=svg_content, media_type="image/svg+xml")

    return FileResponse(favicon_path)


# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)

# Get paths
PROJECT_ROOT = Path(__file__).parent.parent
LANDING_PATH = PROJECT_ROOT / "eventaic-frontend" / "landing"
APP_PATH = PROJECT_ROOT / "eventaic-frontend" / "app" / "dist"
STATIC_PATH = PROJECT_ROOT / "static"

# Ensure directories exist
STATIC_PATH.mkdir(exist_ok=True)
(STATIC_PATH / "images" / "ads").mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")

# Mount landing page assets
if LANDING_PATH.exists():
    app.mount("/assets", StaticFiles(directory=str(LANDING_PATH / "assets")), name="landing_assets")

# Mount Vue app static files if built
if APP_PATH.exists():
    app.mount("/app/assets", StaticFiles(directory=str(APP_PATH / "assets")), name="app_assets")


    @app.get("/app/{full_path:path}")
    async def serve_app(full_path: str):
        """Serve Vue app for all /app routes"""
        index_file = APP_PATH / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse(
            content="App not built. Run 'npm run build' in eventaic-frontend/app",
            status_code=404
        )
else:
    @app.get("/app/{full_path:path}")
    async def redirect_to_dev(full_path: str):
        """Redirect to Vite dev server in development"""
        if settings.is_development:
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
        return HTMLResponse(
            content="App not available. Please build the frontend.",
            status_code=503
        )


@app.get("/")
async def serve_landing():
    """Serve landing page at root"""
    landing_file = LANDING_PATH / "index.html"

    if landing_file.exists():
        with open(landing_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # Fix asset paths
        content = content.replace('href="assets/', 'href="/assets/')
        content = content.replace('src="assets/', 'src="/assets/')
        return HTMLResponse(content=content)
    else:
        # Simple fallback landing page
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
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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


# Startup event logger
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 50)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info(f"API Docs: {'/api/docs' if settings.DEBUG else 'Disabled'}")
    logger.info("=" * 50)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
