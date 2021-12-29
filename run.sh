# apt-get install python3-venv
# apt-get install libpangocairo-1.0-0
#
# pour oracle cloud, il faut ouvrir les ports 5000 du firewall : https://docs.oracle.com/en-us/iaas/developer-tutorials/tutorials/apache-on-ubuntu/01oci-ubuntu-apache-summary.htm
# 
python3 -m venv ./env
source ./env/bin/activate
mkdir -p ./var

pip install --upgrade pip
pip install -r requirements.txt
export FLASK_ENV=development
export FLASK_APP=app
flask run flask run --host=0.0.0.0
