# El artesano

Stack base:
- Python 3.13
- Django 5.2.9
- PostgreSQL

Instalacion sugerida:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
