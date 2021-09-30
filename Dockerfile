FROM python:2.7

WORKDIR /usr/src/app

COPY ./techtrends ./
RUN pip install -r requirements.txt

EXPOSE 3111

CMD [ "python", "./init_db.py" ]
CMD [ "python", "./app.py" ]