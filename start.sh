sudo python3 manage.py makemigrations
sudo python3 manage.py migrate
pip3 install -r requirements.txt
nohup python3 manage.py runserver 0.0.0.0:5000 &
