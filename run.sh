python3 -m venv ./env
source ./env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export FLASK_ENV=development
export FLASK_APP=app
flask run