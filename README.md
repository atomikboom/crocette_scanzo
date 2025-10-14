# Dashboard Crocette (v2 con login visibile e regolamento testo)

## Avvio rapido
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python -c "from app.seed import init_db; init_db()"
python -m uvicorn app.main:app --reload

Login: admin / admin123
