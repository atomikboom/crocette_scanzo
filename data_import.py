
"""
Importa:
- Nomi squadra
- Movimenti iniziali (crocette già date) come addebiti
- Aggiorna/crea Regolamento 2025/2026
- Copia (opzionale) il PDF Calendario Paste in app/static (se presente accanto a questo script)
Esegui:  python data_import.py
"""

from datetime import datetime
import os, shutil
from app.database import SessionLocal, engine
from app.models import User, Member, Rule, Movement
from app.auth import hash_password

# --- Config ---
CREATE_ADMIN_IF_MISSING = True
ADMIN_USER = ("admin", "admin123")  # username, password

NAMES = [
    "Cri","Dani","Rese","Mirco","Gio","Franco","Cino","Iliass","Pinna","Pietro","Omar","Bolla","Nobile","Cassi"
]

MOVEMENTS = [
    ("Dani","Matrimonio",10),
    ("Dani","Concerto",10),
    ("Pietro","Lesione ai compagni",1),
    ("Nobile","Assenza allenamenti",60),
    ("Pinna","Calzini sbagliati primo allenamento",1),
    ("Pietro","Calcio al pallone e pallonata a compagno",2),
    ("Cassi","Ritardo avviso per assenza allenamento",5),
    ("Cassi","Ritardo avviso per assenza allenamento",2),
    ("Pietro","Gesto di stizza (pugno al palo)",1),
    ("Pinna","Paste in battuta",10),
    ("Pietro","Gesto di stizza sul carrello",1),
    ("Pietro","Fuma in palestra x2",2),
    ("Pietro","Calcio alla porta",1),
    ("Mirco","Dimenticanza pantaloncini",1),
    ("Nobile","Battuta sotto rete",10),
    ("Iliass","Gesto di stizza",1),
    ("Iliass","Battuta sotto rete",10),
    ("Rese","Gesto di stizza bagherone",1),
    ("Mirco","Dimenticanza felpa",1),
    ("Mirco","Procurato spavento (nausea)",1),
    ("Mirco","Gesto di stizza calcio alla bottiglietta + negazione",2),
    ("Iliass","Pugno al palo",1),
    ("Pietro","Gesto di stizza",1),
    ("Pietro","Assenza amichevole",10),
    ("Cri","Ginocchiere prestate",1),
    ("Franco","Battuta sotto rete",10),
    ("Pietro","Battuta sulla palestina",1),
    ("Pietro","Dimenticanza borsone",1),
    ("Rese","Insulto capitano",4),
    ("Gio","Procurato spavento",1),
    ("Iliass","Dimenticanza maglia riscaldamento",2),
]

# Regolamento 2025/2026 – voci principali (valori fissi); le parti variabili restano in descrizione
RULES = [
    ("Ritardo con avviso e motivazione valida", "Nessuna crocetta se segnalato almeno 30 min prima.", 0, 0),
    ("Ritardo non avvisato", "1 crocetta per i primi 5 min, poi 1/min fino a 20 (allenamenti/video/partite/eventi).", 0, 0),
    ("Ritardo Ritrovo/Partita", "2 crocette per i primi 5 min, poi 2/min fino a 40.", 0, 0),
    ("Assenza allenamento (ingiustificata)", "Esempi: vacanza, matrimonio, cena non di lavoro ecc.", 10, 0),
    ("Assenza allenamento (lavoro)", "Per cena di lavoro: 1 crocetta.", 0, 0),
    ("Assenza allenamento (malattia)", "", 0, 0),
    ("Assenza partita (non malattia)", "", 20, 0),
    ("Dimenticanza capo/accessorio societario", "Allenamento: maglia gialla Errea e pantaloncini blu Errea obbligatori.", 1, 0),
    ("Omertà su noleggio capo societario", "2 crocette al dimenticante (oltre a quella base) e 2 al prestatore.", 2, 0),
    ("Oggetto personale smarrito", "In palestra/spogliatoio/ritrovo.", 1, 0),
    ("Cartellino giallo", "", 2, 0),
    ("Cartellino rosso", "", 10, 0),
    ("Sottorete allenamento", "", 10, 0),
    ("Sottorete partita", "", 20, 0),
    ("Occasioni speciali", "Laurea, matrimonio, patente, nascita figli, auto/casa nuova ecc.", 10, 0),
    ("Scarpe dimenticate (allenamento)", "", 3, 0),
    ("Scarpe dimenticate (partita)", "", 10, 0),
    ("Suoneria in allenamento", "", 1, 0),
    ("Suoneria durante video", "", 2, 0),
    ("Spreco alcool consistente", ">= 5 cl", 1, 0),
    ("Dimenticanza documento identità (partita)", "", 10, 0),
    ("Gesto di stizza", "", 1, 0),
    ("Diffamazioni / Omertà / Falsa testimonianza", "", 1, 0),
    ("Esordio in Serie B", "", 10, 0),
    ("Nomina di Capitano", "", 10, 0),
    ("Sanzioni generale", "Giorno partita: tutte le crocette raddoppiate (escluso giallo). Valore crocetta: 2€.", 0, 0),
]

def upsert_rule(db, title, description, crocette, casse):
    r = db.query(Rule).filter(Rule.title == title).first()
    if r:
        r.description = description
        r.crocette = crocette
        r.casse = casse
    else:
        r = Rule(title=title, description=description, crocette=crocette, casse=casse)
        db.add(r)
    return r

def main():
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # admin di default (se mancante)
        if CREATE_ADMIN_IF_MISSING and not db.query(User).filter_by(username=ADMIN_USER[0]).first():
            db.add(User(username=ADMIN_USER[0], password_hash=hash_password(ADMIN_USER[1]), role="admin"))
            print("Creato admin di default:", ADMIN_USER[0])

        # membri
        for name in NAMES:
            if not db.query(Member).filter_by(name=name).first():
                db.add(Member(name=name))
        db.commit()

        # regole
        for t,d,c,k in RULES:
            upsert_rule(db, t,d,c,k)
        db.commit()

        # movimenti iniziali
        # assoceremo i movimenti all'admin se esiste, altrimenti al primo utente
        admin = db.query(User).filter_by(username=ADMIN_USER[0]).first() or db.query(User).first()
        if not admin:
            raise RuntimeError("Nessun utente presente: crea prima un utente admin.")

        name_to_id = {m.name: m.id for m in db.query(Member).all()}
        inserted = 0
        for nome, motivo, n in MOVEMENTS:
            mid = name_to_id.get(nome)
            if not mid:
                print("ATTENZIONE: nome non trovato, salto:", nome)
                continue
            mv = Movement(member_id=mid, user_id=admin.id, kind="debit",
                          crocette=int(n), casse=0, note=motivo)
            db.add(mv)
            inserted += 1
        db.commit()
        print(f"Inseriti {inserted} movimenti.")

        # Copia PDF calendario se presente accanto allo script
        src_pdf = os.path.join(os.path.dirname(__file__), "Calendario_Paste_2025_2026.pdf")
        dst_pdf = os.path.join(os.path.dirname(__file__), "app", "static", "Calendario_Paste_2025_2026.pdf")
        if os.path.exists(src_pdf):
            os.makedirs(os.path.dirname(dst_pdf), exist_ok=True)
            shutil.copy2(src_pdf, dst_pdf)
            print("Calendario Paste copiato in:", dst_pdf)
        else:
            print("Calendario Paste NON trovato accanto allo script (opzionale).")

        print("FATTO ✔")
    finally:
        db.close()

if __name__ == "__main__":
    main()
