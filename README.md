# Django Basic Commands

* To Start the project

        django-admin startproject project-Name
    
* To Start the app

        python manage.py startapp app-Name
    
* Active the environment with below cmd:
    
        source venv/bin/activate
    
* Migration Commands

        python manage.py makemigrations webApi
        python manage.py migrate webApi 0001
        
* To Start Django 
        
        python manage.py runserver 0.0.0.0:8080

* if you find **any egg_info error** needs to install 
    
        libmysqlclient-dev     
