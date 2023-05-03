FROM python:3.10
# FROM ubuntu:latest

EXPOSE 5000
EXPOSE 80

COPY requirements.txt requirements.txt
# RUN pip install -r requirements.txt


# RUN apt-get update && \
#       apt-get -y install sudo
# RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
# USER docker
# CMD /bin/bash

# RUN apt-get update && apt-get install build-essential cmake --no-install-recommends

# RUN apt-get install python3.9

RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# CMD ["python", "-m" , "flask" , "run",  "--host=0.0.0.0"]
CMD ["python", "-u","app.py"]

#docker build -t testo:flasko .
#docker run --name testo -p 5000:5000 -p 80:80 testo:flasko