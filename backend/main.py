from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import create_db_and_tables
from routes.scraper_routes import router as scraper_router
from routes.ai_routes import router as ai_router
from routes.auth_routes import router as auth_router

create_db_and_tables()
    

app = FastAPI(
    title="Webscraper API",
    description="A simple API to provide App Recommendations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)


app.include_router(scraper_router)
app.include_router(ai_router)
app.include_router(auth_router) 

@app.get("/")
def read_root():
    return {"Hello": "World", "message": "WebAnalyzer API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
