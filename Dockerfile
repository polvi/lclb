from base
run apt-get update
run apt-get install -y python-pip
run pip install apache-libcloud
run mkdir /app/
workdir /app/
add cacert.pem /app/
add config.py /app/
add lclb.py /app/
