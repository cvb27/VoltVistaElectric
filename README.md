# Voltvista Web (FastAPI + Jinja2 + Bootstrap)

## 1) Setup local
```bash
cd voltvista-web
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edita .env con tus datos y llaves

uvicorn app.main:app --reload
