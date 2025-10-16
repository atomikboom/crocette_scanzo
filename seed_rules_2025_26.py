# seed_rules_2025_26.py
# Esegui:  python seed_rules_2025_26.py
from app.database import SessionLocal
from app.models import Rule

rules = [
    # 1. RITARDI
    dict(title="1A. Ritardo con avviso (≥30 min prima)", description="Nessuna crocetta se segnalato almeno 30 min prima.", crocette=0),
    dict(title="1B. Ritardo non avvisato", description="1 crocetta per i primi 5 min; poi 1/min fino a max 20.", crocette=0),
    dict(title="1C. Ritardo ritrovo/partita", description="2 crocette per i primi 5 min; poi 2/min fino a max 40.", crocette=0),
    dict(title="Nota ritardi", description="Si applica ad allenamenti, video, partite o eventi di squadra; esclusa solo la sala pesi.", crocette=0),

    # 1-bis. ASSENZE
    dict(title="Assenza allenamento (ingiustificata)", description="Vacanza, matrimonio, cena non di lavoro ecc.", crocette=10),
    dict(title="Assenza allenamento (lavoro)", description="Per cena di lavoro vedere regola dedicata.", crocette=0),
    dict(title="Cena di lavoro", description="Assenza per cena di lavoro.", crocette=1),
    dict(title="Assenza allenamento (malattia)", description="Giustificata per malattia.", crocette=0),
    dict(title="Assenza partita", description="Per malattia 0 crocette (vedi regola dedicata).", crocette=20),
    dict(title="Assenza partita (malattia)", description="", crocette=0),

    # 2. ABBIGLIAMENTO
    dict(title="Dimenticanza capo richiesto", description="1 crocetta per ogni articolo dimenticato (maglia/pantaloncini ecc.).", crocette=1),
    dict(title="Omertà noleggio capo — dimenticante", description="+2 oltre alla dimenticanza.", crocette=2),
    dict(title="Omertà noleggio capo — prestatore", description="+2 per il prestatore.", crocette=2),

    # 2-bis
    dict(title="Oggetto personale smarrito", description="Oggetto perso in palestra/spogliatoio/ritrovo.", crocette=1),

    # 3. PASTE
    dict(title="Dolce extra nel turno di altri (credito)", description="Usare 'credit' in inserimento movimento.", crocette=10),

    # 4. CARTELLINI
    dict(title="Cartellino giallo", description="NON si raddoppia nel giorno partita.", crocette=2),
    dict(title="Cartellino rosso", description="Già considerato doppio per partita: NON applicare ulteriore raddoppio.", crocette=10),

    # 5. SOTTO RETE
    dict(title="Sottorete (allenamento)", description="", crocette=10),
    dict(title="Sottorete (partita)", description="", crocette=20),

    # 6. OCCASIONI SPECIALI
    dict(title="Occasioni speciali", description="Laurea, proprio matrimonio, patente, nascita figli, auto/casa nuova ecc.", crocette=10),

    # 7. SCARPE
    dict(title="Dimenticanza scarpe (allenamento)", description="", crocette=3),
    dict(title="Dimenticanza scarpe (partita)", description="", crocette=10),

    # 8. SUONERIA
    dict(title="Suoneria in allenamento", description="", crocette=1),
    dict(title="Suoneria durante video", description="", crocette=2),

    # 9.
    dict(title="Spreco alcool consistente (≥5 cl)", description="", crocette=1),

    # 10.
    dict(title="Dimenticanza documento identità (partita)", description="", crocette=10),

    # 12.
    dict(title="Gesto di stizza", description="", crocette=1),

    # 13.
    dict(title="Diffamazioni / Omertà / Falsa testimonianza", description="", crocette=1),

    # 14–15.
    dict(title="Esordio in Serie B", description="", crocette=10),
    dict(title="Nomina di capitano", description="", crocette=10),

    # SANZIONI / POLICY (informative)
    dict(title="Altro", description="", crocette=1),
]

def main():
    s = SessionLocal()
    try:
        s.query(Rule).delete()
        s.commit()
        for r in rules:
            s.add(Rule(title=r["title"], description=r["description"], crocette=r["crocette"], casse=0))
        s.commit()
        print(f"OK ✔ Inserite {len(rules)} regole.")
    finally:
        s.close()

if __name__ == "__main__":
    main()
