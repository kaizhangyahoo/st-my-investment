FROM python:3.11-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -U pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8501/tcp
ENTRYPOINT [ "/usr/local/bin/streamlit", "run", "streamlit_login.py" ]