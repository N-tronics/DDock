FROM ubuntu:latest

ENV DDD_CONF /etc/ddd.conf.json

# The dist/ has all the compiled programs
COPY dist/ /bin/
COPY ddd.conf.json /etc

# Run the ddock daemon on startup
CMD ["./bin/ddock-daemon"]