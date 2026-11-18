import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Depends, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.config import settings
from app.database import Base, engine, SessionLocal, get_db
from app.models import Death
from app.security import is_authenticated, password_matches
from app.scraper import fetch_deaths
from app.telegram import send_alert

Path("data").mkdir(exist_ok=True)

class Connections:
    def __init__(self): self.clients = set()
    async def connect(self, ws):
        await ws.accept()
        self.clients.add(ws)
    def disconnect(self, ws): self.clients.discard(ws)
    async def broadcast(self, payload):
        stale = []
        for ws in list(self.clients):
            try: await ws.send_json(payload)
            except Exception: stale.append(ws)
        for ws in stale: self.disconnect(ws)

connections = Connections()

async def polling_loop():
    while True:
        try:
            rows = await fetch_deaths()
            with SessionLocal() as db:
                for item in rows:
                    if db.scalar(select(Death.id).where(Death.source_key == item["source_key"])): continue
                    death = Death(**item)
                    db.add(death)
                    db.commit()
                    payload = {"id": death.id, "victim": death.victim, "level": death.level,
                               "killer": death.killer, "guild": death.guild,
                               "happened_at": death.happened_at.isoformat() if death.happened_at else None}
                    await connections.broadcast({"type": "death", "death": payload})
                    if death.guild in ("ally", "enemy"):
                        label = settings.guild_ally if death.guild == "ally" else settings.guild_enemy
                        when = death.happened_at.strftime("%d/%m/%Y %H:%M") if death.happened_at else "horário não identificado"
                        msg = f"⚠️ Death Radar – Aurera Global\nGuild: {label}\nPersonagem: {death.victim}\nLevel: {death.level or 'não identificado'}\nMatadores: {death.killer or 'não identificado'}\nData: {when}"
                        try: await send_alert(msg)
                        except Exception as exc: print(f"Telegram alert failed: {exc}")
        except Exception as exc:
            print(f"Death polling failed: {exc}")
        await asyncio.sleep(settings.poll_interval_seconds)

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(polling_loop())
    yield
    task.cancel()
    try: await task
    except asyncio.CancelledError: pass

app = FastAPI(title="Death Radar – Aurera Global", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key or "local-development-key-change-me", https_only=False, same_site="lax")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
async def health(): return {"status": "ok"}

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("authenticated"): return RedirectResponse("/", status_code=303)
    return HTMLResponse(Path("static/login.html").read_text(encoding="utf-8"))

@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if not password_matches(password, settings.admin_password):
        html = Path("static/login.html").read_text(encoding="utf-8").replace("<!--ERROR-->", '<p class="error">Senha inválida.</p>')
        return HTMLResponse(html, status_code=401)
    request.session["authenticated"] = True
    return RedirectResponse("/", status_code=303)

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not request.session.get("authenticated"): return RedirectResponse("/login", status_code=303)
    return HTMLResponse(Path("static/index.html").read_text(encoding="utf-8"))

@app.get("/api/summary")
async def summary(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("authenticated"): return JSONResponse({"error":"unauthorized"}, status_code=401)
    total = db.scalar(select(func.count(Death.id))) or 0
    enemy = db.scalar(select(func.count(Death.id)).where(Death.guild == "enemy")) or 0
    ally = db.scalar(select(func.count(Death.id)).where(Death.guild == "ally")) or 0
    unknown = db.scalar(select(func.count(Death.id)).where(Death.guild == "unknown")) or 0
    return {"total": total, "enemy": enemy, "ally": ally, "unknown": unknown}

@app.get("/api/deaths")
async def deaths(request: Request, limit: int = 100, db: Session = Depends(get_db)):
    if not request.session.get("authenticated"): return JSONResponse({"error":"unauthorized"}, status_code=401)
    rows = db.scalars(select(Death).order_by(Death.id.desc()).limit(min(max(limit, 1), 500))).all()
    return [{"id":x.id,"victim":x.victim,"level":x.level,"killer":x.killer,"guild":x.guild,
             "raw_text":x.raw_text,"happened_at":x.happened_at.isoformat() if x.happened_at else None,
             "created_at":x.created_at.isoformat() if x.created_at else None} for x in rows]

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    if not ws.session.get("authenticated"):
        await ws.close(code=1008)
        return
    await connections.connect(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: connections.disconnect(ws)
