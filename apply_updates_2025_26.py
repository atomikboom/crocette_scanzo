# apply_updates_2025_26.py
# Esegui:  python apply_updates_2025_26.py
from app.database import SessionLocal, engine, Base
from app.models import User, Member, Movement
from app.auth import hash_password

from datetime import datetime

# ========== DATI ==========
NEW_NAMES = [
    "Cri","Dani","Rese","Mirco","Gio","Franco","Cino","Iliass",
    "Pinna","Pietro","Omar","Bolla","Nobile","Cassi",
]

# Crocette PRESE (=> debiti)
CROCETTE_PRESE = [
    ("Dani",   "Matrimonio",                                   10),
    ("Dani",   "Concerto",                                     10),
    ("Pietro", "Lesione ai compagni",                           1),
    ("Nobile", "Assenza allenamenti",                          60),
    ("Pinna",  "Calzini sbagliati primo allenamento",           1),
    ("Pietro", "Calcio al pallone e pallonata a compagno",      2),
    ("Cassi",  "Ritardo avviso per assenza allenamento",        5),
    ("Cassi",  "Ritardo avviso per assenza allenamento",        2),
    ("Pietro", "Gesto di stizza (pugno al palo)",               1),
    ("Pinna",  "Paste in battuta",                             10),
    ("Pietro", "Gesto di stizza sul carrello",                  1),
    ("Pietro", "Fuma in palestra x2",                           2),
    ("Pietro", "Calcio alla porta",                             1),
    ("Mirco",  "Dimenticanza pantaloncini",                     1),
    ("Nobile", "Battuta sotto rete",                           10),
    ("Iliass", "Gesto di stizza",                               1),
    ("Iliass", "Battuta sotto rete",                           10),
    ("Rese",   "Gesto di stizza bagherone",                     1),
    ("Mirco",  "Dimenticanza felpa",                            1),
    ("Mirco",  "Procurato spavento (nausea)",                   1),
    ("Mirco",  "Gesto di stizza calcio alla bottiglietta + negazione", 2),
    ("Iliass", "Pugno al palo",                                 1),
    ("Pietro", "Gesto di stizza",                               1),
    ("Pietro", "Assenza amichevole",                           10),
    ("Cri",    "Ginocchiere prestate",                          1),
    ("Franco", "Battuta sotto rete",                           10),
    ("Pietro", "Battuta sulla palestina",                       1),
    ("Pietro", "Dimenticanza borsone",                          1),
    ("Rese",   "Insulto capitano",                              4),
    ("Gio",    "Procurato spavento",                            1),
    ("Iliass", "Dimenticanza maglia riscaldamento",             2),
]

# Crocette PAGATE (=> crediti totali per persona)
CROCETTE_PAGATE = {
    "Cri":    0,
    "Dani":   22,
    "Rese":   0,
    "Mirco":  14,
    "Gio":    0,
    "Franco": 0,
    "Cino":   11,
    "Iliass": 10,
    "Pinna":  0,
    "Pietro": 0,
    "Omar":   0,
    "Bolla":  0,
    "Nobile": 0,
    "Cassi":  0,
}

ADMIN_USER = ("admin", "admin123")  # se manca l'admin lo creo

# ========== IMPL ==========
def soft_reset_members_and_movements(db):
    # Prima cancelliamo i movimenti (hanno FK su members)
    db.query(Movement).delete()
    # Poi azzeriamo i membri
    db.query(Member).delete()
    db.commit()

def ensure_admin(db):
    u = db.query(User).filter(User.username == ADMIN_USER[0]).first()
    if not u:
        u = User(username=ADMIN_USER[0], password_hash=hash_password(ADMIN_USER[1]), role="admin")
        db.add(u)
        db.commit()
        db.refresh(u)
    return u

def main():
    db = SessionLocal()
    try:
        # 1) Soft reset di members+movements (mantiene utenti e regole)
        soft_reset_members_and_movements(db)

        # 2) Admin (serve per attribuire i movimenti)
        admin = ensure_admin(db)

        # 3) Inserisci nuovi membri
        name_to_id = {}
        for n in NEW_NAMES:
            m = Member(name=n)
            db.add(m); db.commit(); db.refresh(m)
            name_to_id[n] = m.id

        # 4) Inserisci crocette PRESE (debit)
        now = datetime.now()
        for nome, nota, croc in CROCETTE_PRESE:
            mid = name_to_id.get(nome)
            if not mid:
                print(f"[WARN] Nome non presente in NEW_NAMES, salto debit: {nome} - {nota} ({croc})")
                continue
            mv = Movement(
                member_id=mid,
                user_id=admin.id if admin else None,
                kind="debit",
                crocette=int(croc),
                casse=0,
                note=nota,
                created_at=now  # puoi cambiare a data specifica se vuoi
            )
            db.add(mv)
        db.commit()

        # 5) Inserisci crocette PAGATE (credit totali)
        for nome, tot in CROCETTE_PAGATE.items():
            if not tot:  # zero -> niente movimento
                continue
            mid = name_to_id.get(nome)
            if not mid:
                print(f"[WARN] Nome non presente in NEW_NAMES, salto credit: {nome} ({tot})")
                continue
            mv = Movement(
                member_id=mid,
                user_id=admin.id if admin else None,
                kind="credit",
                crocette=int(tot),
                casse=0,
                note="Pagate da inizio anno",
                created_at=now
            )
            db.add(mv)
        db.commit()

        print("OK ✔  Dati aggiornati.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
