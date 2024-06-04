# services/ui/Dockerfile
FROM continuumio/anaconda3

WORKDIR /usr/src/app

RUN conda install faiss-cpu

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sleep", "infinity"]
