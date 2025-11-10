from fastapi import FastAPI, Depends, Request, Response, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os, re

from .database import Base, engine, get_db
from .models import User, Member, Rule, Movement, BagheroneScore
from .auth import create_access_token, verify_password, get_current_user

from jose import jwt, JWTError
from .auth import SECRET_KEY, ALGORITHM

# ------------ CONFIG PATHS ------------
APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
CAL_TXT = os.path.join(DATA_DIR, "calendar.txt")

# ------------ FASTAPI APP ------------
app = FastAPI(title="Dashboard Crocette")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
Base.metadata.create_all(bind=engine)

# ------------ UTILS ------------
MONTHS_IT = {
    "gen":1, "gennaio":1, "feb":2, "febbraio":2, "mar":3, "marzo":3, "apr":4, "aprile":4,
    "mag":5, "maggio":5, "giu":6, "giugno":6, "lug":7, "luglio":7, "ago":8, "agosto":8,
    "set":9, "sett":9, "settembre":9, "ott":10, "ottobre":10, "nov":11, "novembre":11,
    "dic":12, "dicembre":12,
}

EMOJIS = {"paste":"🍕", "home":"🏠", "away":"✈️", "birthday":"🎂"}
EMOJI_SET = set(EMOJIS.values())

from datetime import timezone

def now_utc():
    return datetime.now(timezone.utc)


def get_optional_user(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.username == username, User.is_active == True).first()

def aggregate(db: Session):
    # Solo crocette
    debits  = db.query(Movement).filter(Movement.kind == "debit",  Movement.deleted_at.is_(None)).all()
    credits = db.query(Movement).filter(Movement.kind == "credit", Movement.deleted_at.is_(None)).all()

    deb_croc = sum(m.crocette for m in debits)
    cre_croc = sum(m.crocette for m in credits)
    return {
        "crocette_prese_total": deb_croc,
        "crocette_pagate": cre_croc,
        "crocette_da_pagare": max(0, deb_croc - cre_croc),
    }

# ------------ CALENDAR (SOLO TESTO LOCALE) ------------
DEFAULT_CALENDAR = """\
# Esempi (una riga per evento). Modifica liberamente:
# 2025-10-14 🍕 Dani
# 2025-10-18 🏠 Scanzo vs XYZ
# 2025-10-25 ✈️ Trasferta vs ABC
# 2025-11-02 🎂 Mirco
"""

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def parse_date_any(s: str):
    s = s.strip().lower()
    m = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m:
        y, mo, d = map(int, m.groups())
        return datetime(y, mo, d)
    m = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", s)
    if m:
        d, mo, y = m.groups()
        d, mo, y = int(d), int(mo), int(y)
        if y < 100: y += 2000
        return datetime(y, mo, d)
    m = re.search(r"(\d{1,2})\s+([a-zà]+)(?:\s+(\d{4}))?", s)
    if m:
        d = int(m.group(1)); mm = m.group(2).strip("."); y = m.group(3)
        mo = MONTHS_IT.get(mm, None)
        if mo:
            if y: y = int(y)
            else: y = 2025 if mo >= 8 else 2026
            return datetime(y, mo, d)
    return None

def normalize_line(line: str):
    return re.sub(r"\s+", " ", line).strip()

def parse_calendar_text(text: str):
    ev = []
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        line = normalize_line(raw)
        found = next((e for e in EMOJI_SET if e in line), None)
        if not found:
            continue
        d = parse_date_any(line) or parse_date_any(line.split(found, 1)[0])
        if d is None:
            continue
        after = line.split(found, 1)[1].strip(" -:—").strip()
        typ = "paste" if found == EMOJIS["paste"] else ("home" if found == EMOJIS["home"] else ("away" if found == EMOJIS["away"] else "birthday"))
        ev.append({"date": d, "type": typ, "who": after, "emoji": found, "raw": raw})
    ev.sort(key=lambda x: x["date"])
    return ev

def load_calendar_text():
    ensure_data_dir()
    if not os.path.exists(CAL_TXT):
        with open(CAL_TXT, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CALENDAR)
    with open(CAL_TXT, "r", encoding="utf-8") as f:
        return f.read()

def save_calendar_text(text: str):
    ensure_data_dir()
    with open(CAL_TXT, "w", encoding="utf-8") as f:
        f.write(text or "")

def get_or_create_bagherone(db: Session) -> BagheroneScore:
    row = db.query(BagheroneScore).first()
    if not row:
        row = BagheroneScore(giovani=0, vecchi=0)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


# ------------ ROUTES ------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    rules = db.query(Rule).filter(Rule.active == True).all()
    members = db.query(Member).all()
    bagherone = get_or_create_bagherone(db)

    rows = []
    for m in members:
        deb_croc = sum(x.crocette for x in m.movements if x.kind == "debit" and x.deleted_at is None)
        cre_croc = sum(x.crocette for x in m.movements if x.kind == "credit" and x.deleted_at is None)
        last_dt  = max([x.created_at for x in m.movements if x.deleted_at is None], default=None)

        rows.append({
            "id": m.id,
            "name": m.name,
            "crocette_prese": deb_croc,
            "crocette_pagate": cre_croc,
            "crocette_da_pagare": max(0, deb_croc - cre_croc),
            "last": max([x.created_at for x in m.movements], default=None)
        })

    totals = aggregate(db)
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    last_month = (
        db.query(Movement)
          .filter(Movement.deleted_at.is_(None))
          .filter(Movement.created_at >= month_start)
          .order_by(Movement.created_at.desc())
          .limit(50)
          .all()
    )
    latest_movement = (
        db.query(Movement)
          .filter(Movement.deleted_at.is_(None))
          .order_by(Movement.created_at.desc())
          .first()
    )
    user = get_optional_user(request, db)

    cal_text = load_calendar_text()
    events = parse_calendar_text(cal_text)
    upcoming_pastes = [e for e in events if e["type"] == "paste" and e["date"] >= now][:5]
    matches = [e for e in events if e["type"] in ("home", "away") and e["date"] >= now]
    next_match = matches[0] if matches else None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "rules": rules,
        "rows": rows,
        "totals": totals,
        "last_month": last_month,
        "latest_movement": latest_movement,
        "user": user,
        "calendar_text": cal_text,
        "upcoming_pastes": upcoming_pastes,
        "next_match": next_match,
        "bagherone" : bagherone,
    })

@app.get("/storico", response_class=HTMLResponse)
async def storico(request: Request,
                  kind: str = "debit",
                  member_id: int | None = None,
                  db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    members = db.query(Member).order_by(Member.name).all()

    q = db.query(Movement).filter(Movement.deleted_at.is_(None)).order_by(Movement.created_at.desc())
    kind = kind.lower().strip()
    if kind in ("debit", "credit"):
        q = q.filter(Movement.kind == kind)
    if member_id:
        q = q.filter(Movement.member_id == member_id)

    moves = q.all()
    total_crocette = sum(m.crocette for m in moves)

    return templates.TemplateResponse("history.html", {
        "request": request,
        "moves": moves,
        "members": members,
        "kind": kind,
        "member_id": member_id,
        "total": total_crocette,
        "user": user,
    })

@app.post("/calendar")
async def save_calendar(request: Request, user: User = Depends(get_current_user), text: str = Form(...)):
    if user.role != "admin":
        return RedirectResponse("/", status_code=302)
    save_calendar_text(text)
    return RedirectResponse("/#saldi?calendar=ok", status_code=302)

@app.get("/calendar.txt", response_class=PlainTextResponse)
async def calendar_txt():
    txt = load_calendar_text()
    return PlainTextResponse(txt or "", media_type="text/plain; charset=utf-8")

# -- login/logout/movements/admin invariati --
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    return templates.TemplateResponse("login.html", {"request": request, "user": user})

@app.post("/login")
async def login(response: Response,
                username: str = Form(...),
                password: str = Form(...),
                next: str | None = Form(None),
                db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse("/login?err=1", status_code=status.HTTP_302_FOUND)
    token = create_access_token({"sub": user.username})
    # sicurezza: consenti solo path interni
    target = next if (next and next.startswith("/")) else "/"
    resp = RedirectResponse(url=target, status_code=status.HTTP_302_FOUND)
    resp.set_cookie("access_token", token, httponly=True, max_age=60*60*12, samesite="lax")
    return resp


@app.post("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@app.get("/movements", response_class=HTMLResponse)
async def movements_page(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if not user:
        return RedirectResponse("/login?next=/movements", status_code=302)
    members = db.query(Member).order_by(Member.name).all()
    rules = db.query(Rule).filter(Rule.active == True).order_by(Rule.title).all()
    return templates.TemplateResponse("movements.html", {"request": request, "members": members, "rules": rules, "user": user})

from fastapi import HTTPException

@app.post("/movements/delete")
async def delete_movement(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    movement_id: int = Form(...),
    next: str | None = Form(None),
):
    # Autorizzazione: solo admin (oppure consenti anche all'autore, se vuoi)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin può eliminare")

    mv = db.query(Movement).filter(Movement.id == movement_id).first()
    if not mv:
        raise HTTPException(status_code=404, detail="Movimento non trovato")

    # soft delete
    mv.deleted_at = now_utc()
    db.commit()

    target = next if (next and next.startswith("/")) else "/storico"
    return RedirectResponse(target, status_code=303)


@app.post("/movements/new")
async def new_movement(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db),
                      member_id: int = Form(...), kind: str = Form(...), rule_id: int | None = Form(None),
                      crocette: int = Form(0), note: str = Form("") ):
    mv = Movement(member_id=member_id, user_id=user.id, kind=kind, rule_id=rule_id,
                  crocette=crocette, casse=0, note=note)
    db.add(mv)
    db.commit()
    return RedirectResponse("/movements?ok=1", status_code=status.HTTP_302_FOUND)

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin":
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "members": db.query(Member).order_by(Member.name).all(),
        "rules": db.query(Rule).order_by(Rule.title).all(),
        "bagherone": get_or_create_bagherone(db),
        "user": user,
    })

@app.post("/admin/member")
async def add_member(user: User = Depends(get_current_user), db: Session = Depends(get_db), name: str = Form(...)):
    if user.role != "admin":
        return RedirectResponse("/", status_code=302)
    db.add(Member(name=name))
    db.commit()
    return RedirectResponse("/admin?member=ok", status_code=302)

@app.post("/admin/rule")
async def add_rule(user: User = Depends(get_current_user), db: Session = Depends(get_db),
                   title: str = Form(...), description: str = Form(""), crocette: int = Form(0)):
    if user.role != "admin":
        return RedirectResponse("/", status_code=302)
    db.add(Rule(title=title, description=description, crocette=crocette, casse=0))
    db.commit()
    return RedirectResponse("/admin?rule=ok", status_code=302)

@app.post("/admin/bagherone")
async def update_bagherone(user: User = Depends(get_current_user),
                           db: Session = Depends(get_db),
                           giovani: int = Form(...),
                           vecchi: int = Form(...)):
    if user.role != "admin":
        return RedirectResponse("/", status_code=302)
    row = get_or_create_bagherone(db)
    row.giovani = max(0, int(giovani))
    row.vecchi = max(0, int(vecchi))
    db.commit()
    return RedirectResponse("/admin?bagherone=ok", status_code=302)
