from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_302_FOUND
from .i18n import load_translations, get_translations
import smtplib
from email.message import EmailMessage
from .models import Transcription
import os
from dotenv import load_dotenv
from .auth import create_default_user
from .database import AsyncSessionLocal

from fastapi import Query
from sqlalchemy import select, func
from sqlalchemy.future import select

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

def send_email_transcription(to_email, transcription):
    msg = EmailMessage()
    msg["Subject"] = "Transcriber Audio"
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = to_email
    msg.set_content(f"{transcription}")

    with smtplib.SMTP_SSL(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")) , timeout=10) as server:
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.send_message(msg)


def get_lang(request: Request) -> str:
    return request.query_params.get("lang") or request.cookies.get("lang") or "pt"

def get_email(request: Request) -> str:
    return request.cookies.get("last_email") or ""

def get_email_checkbox(request: Request) -> str:
    return request.cookies.get("email_checked") or ""

@app.on_event("startup")
async def startup():
    load_translations()
    await init_db()
    
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
        "lang": get_lang(request),
        "user": current_user.username if current_user else None,
        "t": get_translations(get_lang(request)),
        "last_email": get_email(request),
        "last_email_checkbox": get_email_checkbox(request)
    })

    if not current_user:
        response.delete_cookie("access_token")
        response = RedirectResponse("/login", status_code=HTTP_302_FOUND)

    return response

@app.get("/history", response_class=HTMLResponse)
async def transcription_history(
    request: Request,
    page: int = Query(1, ge=1),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    page_size = 10
    offset = (page - 1) * page_size

    result = await db.execute(
        select(Transcription)
        .where(Transcription.user_id == current_user.id)
        .order_by(Transcription.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    transcriptions = result.scalars().all()

    count_result = await db.execute(
        select(func.count(Transcription.id))
        .where(Transcription.user_id == current_user.id)
    )
    total = count_result.scalar()

    return templates.TemplateResponse("history.html", {
        "request": request,
        "lang": get_lang(request),
        "user": current_user.username,
        "transcriptions": transcriptions,
        "page": page,
        "total_pages": (total // page_size) + (1 if total % page_size else 0),
        "t": get_translations(get_lang(request)),
    })

@app.post("/upload")
async def upload_audio(
    request: Request,
    file: UploadFile = File(...),
    send_email: bool = Form(False),
    email: str = Form(""),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        response.delete_cookie("access_token")
        response = RedirectResponse("/login", status_code=HTTP_302_FOUND)
        return response
    
    allowed_extensions = ('.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg', '.oga', '.flac', 'aac')
    if not file.filename.lower().endswith(allowed_extensions):
        return HTMLResponse(
            content="Formato de arquivo não suportado.",
            status_code=400
        )
    transcription = await transcribe_uploaded_file(file)
    transcription_language = ""


    new_transcription = Transcription(
        user_id=current_user.id,
        filename=file.filename,
        text=transcription,
        language=transcription_language
    )
    db.add(new_transcription)
    await db.commit()

    if send_email and email:
        try:
            send_email_transcription(email, transcription)
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "lang": get_lang(request),
        "user": current_user.username,
        "transcription": transcription,
        "t": get_translations(get_lang(request)),
        "last_email": get_email(request),
        "last_email_checkbox": get_email_checkbox(request)
    })
    
    if send_email:
        response.set_cookie(key="last_email",value=email,httponly=True)
        response.set_cookie(key="email_checked",value=send_email,httponly=True)
    else:
        response.delete_cookie("last_email")
        response.delete_cookie("email_checked")

    return response

@app.get("/login")
async def login(
    request: Request,
):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "lang": get_lang(request),
        "login_error": False,
        "t": get_translations(get_lang(request)),
        "last_email": get_email(request),
        "last_email_checkbox": get_email_checkbox(request)
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
            "lang": get_lang(request),
            "login_error": True,
            "t": get_translations(get_lang(request)),
            "last_email": get_email(request),
            "last_email_checkbox": get_email_checkbox(request)
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