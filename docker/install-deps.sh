set -e
apt-get update -y
apt-get install gcc -y

pip install pipenv

apt-get autoremove -y