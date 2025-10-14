from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from .models import User, Rule, Member
from .auth import hash_password

def init_db():
    from .database import Base
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        if not db.query(User).filter_by(username="admin").first():
            db.add(User(username="admin", password_hash=hash_password("admin123"), role="admin"))

        rules = [
            ("Battuta o attacco sotto rete", "", 20, 1),
            ("Compleanno", "", 20, 1),
            ("Rosso in partita", "", 20, 1),
            ("Evento importante", "", 20, 1),
            ("Giallo in partita", "", 4, 0),
            ("Ritardo senza avviso", "1 per i primi 5 minuti, poi 1 al minuto fino a 20", 0, 0),
            ("Ritardo motivato con 2h di anticipo", "", 0, 0),
            ("Ritardo motivato con 1h di anticipo", "", 1, 0),
            ("Falso allarme", "1 (1 bonus mensile)", 1, 0),
            ("Telefono durante i pasti", "", 2, 0),
            ("Gesti di stizza", "", 2, 0),
            ("Assenza per vacanze", "", 5, 0),
            ("Assenze periodo natalizio", "", 10, 0),
            ("Infamata", "", 1, 0),
            ("Spreco di alcol", "", 2, 0),
            ("Dimenticanza materiale societario", "", 2, 0),
            ("Materiale scordato in palestra", "", 1, 0),
            ("Dimenticanza divisa o scarpe in partita", "", 10, 0),
            ("Documento dimenticato", "", 5, 0),
            ("Rutti mentre parla staff", "", 1, 0),
            ("Offesa al capitano", "", 1, 0),
        ]
        if db.query(Rule).count() == 0:
            for t, d, c, k in rules:
                db.add(Rule(title=t, description=d, crocette=c, casse=k))

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
