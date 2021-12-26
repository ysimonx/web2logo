python3 -m venv ./env
source ./env/bin/activate
mkdir -p ./var

pip install --upgrade pip
pip install -r requirements.txt
export FLASK_ENV=development
export FLASK_APP=app
flask run
