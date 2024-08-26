FROM python:3.10.4

WORKDIR /app

ENV FLASK_APP=bioxpress
ENV FLASK_ENV=production 

COPY ./requirements.txt .
RUN pip install -r requirements.txt 

# copy wheel distribution and install it 
COPY ./dist/bioxpress-1.0-py3-none-any.whl .
RUN pip install bioxpress-1.0-py3-none-any.whl

COPY . .

ENTRYPOINT FLASK_APP=bioxpress gunicorn -b :80 'bioxpress:create_app()' --timeout 120 --graceful-timeout 60
