from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import create_db_and_tables
from routes.auth_routes import router as auth_router
from routes.scraper_routes import router as scraper_router
from routes.ai_routes import router as ai_router
from routes.recursive_routes import router as recursive_router
from routes.analysis_routes import router as analysis_router
from routes.export_routes import router as export_router
from routes.health_routes import router as health_router
from routes.dashboard_routes import router as dashboard_router
from routes.issues_routes import router as issues_router 

create_db_and_tables()

app = FastAPI(title="Website Audit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(scraper_router)
app.include_router(ai_router)
app.include_router(recursive_router)
app.include_router(analysis_router)
app.include_router(export_router)
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(issues_router)

@app.get("/")
def read_root():
    return {"message": "Website Audit API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}