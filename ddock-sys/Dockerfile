FROM ubuntu:latest

ENV DDS_CONF=/etc/dds.conf.json
ENV HOME=/root

# The dist/ has all the compiled programs
COPY dist/ /bin/
COPY dds.conf.json /etc

# Run the ddock daemon on startup
CMD ["./bin/ddock-daemon"]