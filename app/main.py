from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_302_FOUND
from .i18n import load_translations, get_translations

import os
from dotenv import load_dotenv
from .auth import create_default_user
from .database import AsyncSessionLocal

from .auth import get_current_user, create_access_token, authenticate_user
from .database import init_db, get_db
from .openai_transcriber import transcribe_uploaded_file

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_lang(request: Request) -> str:
    return request.query_params.get("lang") or request.cookies.get("lang") or "pt"

@app.on_event("startup")
async def startup():
    load_translations()
    await init_db()
    # Carrega usuários do .env
    default_users = os.getenv("DEFAULT_USERS")
    if default_users:
        async with AsyncSessionLocal() as db:
            for pair in default_users.split(","):
                if ":" in pair:
                    username, password = pair.split(":", 1)
                    await create_default_user(db, username.strip(), password.strip())     


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user=Depends(get_current_user)):
    
    response =  templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user.username if current_user else None,
        "t": get_translations(get_lang(request))
    })

    if not current_user:
        response.delete_cookie("access_token")

    return response

@app.post("/upload")
async def upload_audio(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    allowed_extensions = ('.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg', '.oga', '.flac', 'aac')
    if not file.filename.lower().endswith(allowed_extensions):
        return HTMLResponse(
            content="Formato de arquivo não suportado.",
            status_code=400
        )

    transcription = await transcribe_uploaded_file(file)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user.username,
        "transcription": transcription,
        "t": get_translations(get_lang(request))
    })

@app.get("/login")
async def login(
    request: Request,
):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "login_error": False,
        "t": get_translations(get_lang(request))
    })

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(username, password, db)
    if not user:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "login_error": True,
            "t": get_translations(get_lang(request))
        })
    token = create_access_token(user.username)
    response = RedirectResponse(url="/", status_code=HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response