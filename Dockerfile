FROM ubuntu:18.04

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip docker.io git curl && \
    rm -rf /var/lib/apt/lists/* &&\
    curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/darwin/amd64/kubectl && \
    mv kubectl /usr/local/bin && \
    chmod +x /usr/local/bin/kubectl && \
    pip3 install adhesive==0.11.3

