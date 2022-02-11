FROM ubuntu:latest

COPY dist/daemon /bin/ddock-daemon
COPY ddd.conf.json /etc

RUN touch ~/.bash_path
RUN echo "\n. ~/.bash_path" >> ~/.bashrc

CMD ["./bin/ddock-daemon"]