# api.py
# Script for REST API endpoints for DES encryption/decryption

from flask import Flask, request
from flask_restful import Api, Resource
import bitarray
import numpy as np


class Key(Resource):
    def get(self):
        """
        /api/v1/key {GET}

        Generate a random 64-bit key

        Request: N/A

        Response:
            key: String
        """
        return {
            'key': ''.join(map(str, np.random.choice([0, 1], size=(64,))))
        }, 200


# convert 64-bit key to 56-bit key by removing every eighth bit
def get_key_56_bit(key: bitarray.bitarray):
    del_indices = [i*8-1 for i in range(1, 9)]
    for del_ind in reversed(del_indices):
        del key[del_ind]
    return key


def permutation(bits: bitarray.bitarray, permutation_function: dict):
    pass


class Encrypt(Resource):
    def post(self):
        """
        /api/v1/encrypt {POST}

        Encrypt message using DES

        Request:
            message: String (8-character ASCII string)
            key: String (64-character binary string)

        Response:
            cipher: String (64-character binary string)
        """
        # request params
        message = request.form.get('message')
        key = request.form.get('key')

        # convert message and key to bit arrays
        message_bits = bitarray.bitarray()
        message_bits.frombytes(message.encode('utf-8'))
        key_bits = bitarray.bitarray(key)

        # convert 64-bit key to 56-bit key
        key_bits = get_key_56_bit(key_bits)

        # apply initial permutation function to message
        return {
            'cipher': ''
        }, 200


class Decrypt(Resource):
    def post(self):
        """
        /api/v1/decrypt {POST}

        Decrypt cipher using DES

        Request:
            cipher: String (64-character binary string)
            key: String (64-character binary string)

        Response:
            message: String (8-character ASCII string)
        """
        pass


# init app and api
app = Flask(__name__)
api = Api(app)

# endpoint path constants
API_BASE = '/api/v1/'

# attach endpoints
api.add_resource(Key, API_BASE + 'key')
api.add_resource(Encrypt, API_BASE + 'encrypt')
api.add_resource(Decrypt, API_BASE + 'decrypt')


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
