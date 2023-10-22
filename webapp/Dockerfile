FROM python:3.9

WORKDIR /webapp

COPY webapp/. /webapp

COPY .streamlit/ /webapp/.streamlit

COPY database/ /webapp/database

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "streamlit" ]

EXPOSE 8501

CMD [ "run", "--server.address=0.0.0.0", "--server.port=8501", "01_Home.py"]