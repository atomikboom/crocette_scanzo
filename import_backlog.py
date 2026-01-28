import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Member, Movement, User, Rule
from app.database import Base
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# ==========================================================
# CONFIGURAZIONE DATABASE
# ==========================================================
# Se vuoi usare il DB online, assicurati che DATABASE_URL nel file .env 
# punti al database Neon/Render.
# Esempio: postgresql://user:password@hostname/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERRORE: DATABASE_URL non trovato nel file .env")
    exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==========================================================
# DATI DA IMPORTARE (Esempio)
# ==========================================================
# Modifica questa lista con i dati che vuoi aggiungere.
# Formato: (NomeGiocatore, Motivo, Crocette, Tipo ["debit" o "credit"], Data [opzionale])
BACKLOG_STUFF = [
    # ("Nome", "Motivo", Crocette, "debit" o "credit"),
    # Esempio:
    # ("Cri", "Ritardo allenamento", 5, "debit"),
    # ("Dani", "Pagamento parziale", 10, "credit"),
    ("Dani", "Spreco di alcool", 1, "debit"),
    ("Dani", "Insulto alla Merci", 1, "debit"),
    ("Dani", "Elicottero rivolto verso la Merci", 1, "debit"),

    ("Rese", "Spreco di alcool", 1, "debit"),

    ("Nobile", "Spreco di alcool", 1, "debit"),
    ("Nobile", "Insulto alla Merci", 1, "debit"),
    ("Nobile", "Erezione verso Merci", 1, "debit"),

    ("Mirco", "Insulto a pari ruolo", 1, "debit"),

    ("Pietro", "Insulto alla mamma di Mirco", 1, "debit"),
    ("Pietro", "Violenza verso capitano", 1, "debit"),
    ("Pietro", "Insulto alla Merci", 1, "debit"),
    ("Pietro", "Insulto alla mamma di Rese", 1, "debit"),
    ("Pietro", "Insulto contro Maria (bassi toni della voce)", 1, "debit"),
    ("Pietro", "Credito vs Maria (incitamento a strumenti di amplificazione alternativi)", 1, "credit"),
    ("Pietro", "Rottura supporto all'alimentazione alcolica", 5, "debit"),
    ("Pietro", "Insulto a Maria reiterato + insulto a capitano", 3, "debit"),
    ("Pietro", "Effusione sexy con Roberto Bonetti", 1, "credit"),
    ("Pietro", "Lancio di oggetti volanti non identificati", 1, "debit"),

    ("Pietro", "Crocette a credito", 2, "credit"),

    ("Bolla", "IL POETA", 2, "credit"),
    ("Cri", "Bevuto vino a goccia", 10, "credit"),
    ("Omar", "Bevuto vino a goccia", 10, "credit"),
    ("Pietro", "Gesto di stizza", 1, "debit"),
    ("Iliass", "Gesto di stizza", 1, "debit"),
    ("Franco", "Gesto di stizza", 1, "debit"),

    ("Nobile", "Sottorete", 10, "debit"),

    ("Cri", "Dimenticanza cera", 1, "debit"),
    ("Cino", "Dimenticanza borraccia", 1, "debit"),
    ("Franco", "Dimenticanza borraccia", 1, "debit"),
    ("Rese", "Dimenticanza felpa", 1, "debit"),
    ("Rese", "Dimenticanza maglia", 1, "debit"),
    ("Iliass", "Pallonata all'allenatore", 2, "debit"),
    ("Dani", "Dimenticanza ginocchiere", 1, "debit"),
]

def import_data():
    db = SessionLocal()
    try:
        # Recupera l'admin per associare i movimenti
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            print("ERRORE: Nessun utente admin trovato nel database.")
            return

        # Mappa nomi -> id (aggiungiamo alias manuali se necessario)
        members = db.query(Member).all()
        name_to_id = {m.name.lower(): m.id for m in members}
        # Alias comuni
        name_to_id["pie"] = name_to_id.get("pietro")

        # Recupera tutte le regole per provare a fare un match
        rules = db.query(Rule).all()
        
        # Cerchiamo o creiamo una regola generica per i casi non mappati
        generic_rule = db.query(Rule).filter(Rule.title.ilike("%altro%")).first()
        if not generic_rule:
             # Se non esiste, cerchiamo di usarne una generica o la creiamo se admin vuole
             generic_rule = db.query(Rule).filter(Rule.title.ilike("%sanzioni generale%")).first()

        inserted = 0
        for name, note, qty, kind in BACKLOG_STUFF:
            mid = name_to_id.get(name.lower())
            if not mid:
                print(f"ATTENZIONE: Giocatore '{name}' non trovato, salto riga.")
                continue
            
            # Prova a matchare la regola
            matched_rule = None
            note_lower = note.lower()
            for r in rules:
                if r.title.lower() in note_lower or note_lower in r.title.lower():
                    matched_rule = r
                    break
            
            # Se non trovo match, uso la regola generica
            rid = matched_rule.id if matched_rule else (generic_rule.id if generic_rule else None)
            
            mv = Movement(
                member_id=mid,
                user_id=admin.id,
                kind=kind, # "debit" o "credit"
                crocette=int(qty),
                casse=0,
                note=note,
                rule_id=rid,
                created_at=datetime.utcnow()
            )
            db.add(mv)
            inserted += 1
            rule_name = matched_rule.title if matched_rule else (generic_rule.title if generic_rule else "Nessuna")
            print(f"Pronto: {name} - {note} ({qty} {kind}) -> Regola: {rule_name}")

        if inserted > 0:
            confirm = input(f"\nStai per inserire {inserted} nuovi movimenti nel database online. Confermi? (s/n): ")
            if confirm.lower() == 's':
                db.commit()
                print(f"SUCCESSO: {inserted} movimenti inseriti correttamente.")
            else:
                print("Operazione annullata.")
        else:
            print("Nessun dato valido da inserire.")

    except Exception as e:
        print(f"ERRORE durante l'importazione: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print(f"Collegamento al database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'LOCAL'}")
    import_data()
