FROM python:3.10.12
# WORKDIR /app
# COPY . .
# RUN pip install -r requirements.txt
# CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]  
WORKDIR /code 
COPY . . 
RUN pip install -r requirements.txt
# CMD gunicorn yatube.wsgi:application --bind 0.0.0.0:8000
CMD ["gunicorn", "yatube.wsgi:application", "--bind", "0:8000" ] 
