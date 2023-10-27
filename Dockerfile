FROM python:3.11.0

WORKDIR /code 
 
COPY . . 

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt 
 
CMD gunicorn yatube.wsgi:application --bind 0.0.0.0:8000

# CMD ["gunicorn", "api_yamdb.wsgi:application", "--bind", "0:8000" ] 