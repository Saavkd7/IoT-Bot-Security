# CA
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -subj "/CN=MQTT CA" -days 365 -out ca.crt

# Server
openssl genrsa -out server.key 2048
openssl req -new -key server.key -subj "/CN=192.168.10.1" -out server.csr
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365

