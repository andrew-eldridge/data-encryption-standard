# Data Encryption Standard Implementation
Python implementation of the encryption and decryption process of Data Encryption Standard, completed as the final project for Math 587 - Introduction to Cryptography. Group members: Weston Watts, Caroline Boozer, Ellis McLarty, Andrew Eldridge.

Encryption and decryption methods are exposed as REST API endpoints using the Flask-RESTful library.

## Setup
Clone repo
```bash
git clone https://github.com/andrew-eldridge/data-encryption-standard.git
```
Open project directory
```bash
cd data-encryption-standard
```
Run API script
```bash
python api.py
```

## Endpoints
<b>Base address: `127.0.0.1:5000/api/v1`</b>
### /key {GET}
Provides a random 64-bit key to be used for input in the encryption/decryption functions.

Request: N/A

Response:
```json
{
  "key": String
}
```
### /encrypt {POST}
Encrypts given 64-bit (8 character ASCII) message with provided 64-bit (binary) key. Returns corresponding 64-bit (binary) cipher.

Request:
```json
{
  "message": String,
  "key": String
}
```

Response:
```json
{
  "cipher": String
}
```

### /decrypt {POST}
Decrypts given 64-bit (binary) cipher with provided 64-bit (binary) key. Returns corresponding 64-bit (8 character ASCII) message.

Request:
```json
{
  "cipher": String,
  "key": String
}
```

Response:
```json
{
  "message": String
}
```
