# main.py
import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from tools.database import init_db
from routers import auth, users, exams, questions, stats, results

#####################################################################
# == EKLENDİ: UI router import
from routers.ui import ui_router
#####################################################################

app = FastAPI(title="Examination System API (Pydantic Updated)")

# Session Middleware (JWT token’ı session’da tutacağız)
# SECRET_KEY’inizi .env’den de okuyabilirsiniz.
app.add_middleware(SessionMiddleware, secret_key="SESSION_SECRET_KEY", max_age=3600)

# Statik dosyalar (CSS, JS, vs.) için mount
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates (HTML) klasör yolunu tanımla
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def on_startup():
    init_db()

# Mevcut Router’lar (API’ler)
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(exams.router, prefix="/exams", tags=["Exams"])
app.include_router(questions.router, prefix="/questions", tags=["Questions"])
app.include_router(stats.router, prefix="/stats", tags=["Statistics"])
app.include_router(results.router, prefix="/students", tags=["Results"])

#####################################################################
# == EKLENDİ: UI Router (Jinja2 tabanlı web arayüz)
app.include_router(ui_router, tags=["UI Pages"])
#####################################################################

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
