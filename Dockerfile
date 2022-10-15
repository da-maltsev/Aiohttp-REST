FROM library/python:3.6-slim

RUN mkdir /app
WORKDIR /app
COPY . /app


RUN pip3.6 install -r requirements.txt
RUN python3 models.py

EXPOSE 8080

CMD ["python3", "app.py"]

