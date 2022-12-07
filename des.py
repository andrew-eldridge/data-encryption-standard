# des.py
# REST API endpoints for DES encryption/decryption

from flask import Flask, request
from flask_restful import Api, Resource
from const import *
import bitarray
import numpy as np
import argparse


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


# apply permutation function to bitarray, return permuted bitarray
def permutation(bits: bitarray.bitarray, permutation_function: list):
    new_bits = bitarray.bitarray()
    for i in permutation_function:
        new_bits.append(bits[i-1])
    return new_bits


# convert 64-bit key to 56-bit key by removing every eighth bit
def get_key_56_bit(key: bitarray.bitarray):
    del_indices = [i*8-1 for i in range(1, 9)]
    for del_ind in reversed(del_indices):
        del key[del_ind]
    return key


# applies circular left bit shift to bitarray
def circular_left_shift(bits: bitarray.bitarray, shamt: int):
    return bits[shamt:] + bits[:shamt]


# generates keys for each of the 16 rounds of encryption/decryption
def generate_keys(key_bits: bitarray.bitarray):
    keys = []
    # apply PC1 key permutation to produce 56-bit key
    key_bits = permutation(key_bits, PC1)

    if LOG:
        print(f'Key (56-bit) after initial permutation: {key_bits.to01()}')

    for i in range(16):
        # apply bit shift corresponding to curr round to k_l and k_r
        key_bits = circular_left_shift(key_bits[:28], KEY_BIT_SHIFT[i]) + circular_left_shift(key_bits[28:], KEY_BIT_SHIFT[i])
        # apply PC2 key permutation to produce 48-bit round key
        round_key = permutation(key_bits, PC2)
        if LOG:
            print(f'Round key {i} (48-bit) after PC2 permutation: {round_key.to01()}')
        keys.append(round_key)
    return keys


# partitions bitarray into given number of blocks
def partition(bits: bitarray.bitarray, n_blocks: int):
    res = []
    block_size = int(len(bits)/n_blocks)
    for curr_block_ind, next_block_ind in zip(range(n_blocks), range(1, n_blocks+1)):
        res.append(bits[block_size*curr_block_ind:block_size*next_block_ind])
    return res


# combines bit partition into a single bit sequence
def concat_partition(bits_partition: list):
    bits = bitarray.bitarray()
    for bits_i in bits_partition:
        bits = bits + bits_i
    return bits


# exclusive or (XOR) operator for bitarrays
def XOR(b1: bitarray.bitarray, b2: bitarray.bitarray):
    return bitarray.bitarray(''.join([str(int(x) ^ int(y)) for x, y in zip(b1.to01(), b2.to01())]))


# binary to decimal conversion for bitarrays
def bin_to_dec(bits: bitarray.bitarray):
    dec = 0
    for bit in bits:
        dec = (dec << 1) | bit
    return dec


# decimal to binary conversion for bitarrays
def dec_to_bin(dec: int):
    return bitarray.bitarray('{0:04b}'.format(dec))


# perform DES encryption round
def des_round(cipher_bits: bitarray.bitarray, round_key: bitarray.bitarray, i: int):
    # get c_l and c_r from cipher bits
    c_l = cipher_bits[:32]
    c_r = cipher_bits[32:]
    c_r_orig = c_r
    if LOG:
        print(f'Round {i} c_l input: {c_l.to01()}')
        print(f'Round {i} c_r input: {c_r.to01()}')

    # apply expansion permutation to c_r
    c_r = permutation(c_r, EXPANSION_PERMUTATION)
    if LOG:
        print(f'Round {i} c_r after expansion permutation: {c_r.to01()}')

    # XOR between expanded c_r and round key
    c_r = XOR(c_r, round_key)
    if LOG:
        print(f'Round {i} c_r after XOR with round key: {c_r.to01()}')

    # apply S-box substitution to output of expansion permutation
    c_r_partition = partition(c_r, 8)
    if LOG:
        print(f'Round {i} c_r blocks before S-box: {" ".join([c_r_b.to01() for c_r_b in c_r_partition])}')
    for j, c_r_j in enumerate(c_r_partition):
        # get S-box col (bits 1-4) and row (bits 0,5)
        col = bin_to_dec(c_r_j[1:5])
        row = bin_to_dec(c_r_j[0:1] + c_r_j[5:])

        # apply S-box substitution corresponding to col/row to current block
        c_r_partition[j] = dec_to_bin(S_BOX[j][col + row * 16])

    # recombine c_r partition after applying S-box
    if LOG:
        print(f'Round {i} c_r blocks after S-box: {" ".join([c_r_b.to01() for c_r_b in c_r_partition])}')
    c_r = concat_partition(c_r_partition)

    # apply P-box permutation to output of S-box
    c_r = permutation(c_r, P_BOX)
    if LOG:
        print(f'Round {i} c_r after P-box: {c_r.to01()}')

    # XOR between c_l and output of P-box
    c_r = XOR(c_l, c_r)
    if LOG:
        print(f'Round {i} c_r after XOR with c_l: {c_r.to01()}')

    # return output cipher for round
    if LOG:
        print(f'Round {i} output: {c_r_orig.to01()} {c_r.to01()}')
    return c_r_orig + c_r


class Encrypt(Resource):
    def post(self):
        """
        /api/v1/encrypt {POST}

        Encrypt message using DES

        Request:
            message: String (8-character plaintext string)
            key: String (64-character binary string)

        Response:
            cipher: String (64-character binary string)
        """
        # request body
        req_json = request.get_json(force=True)
        message = req_json['message']
        key = req_json['key']

        # convert message and key to bit arrays
        message_bits = bitarray.bitarray()
        message_bits.frombytes(message.encode('utf-8'))
        key_bits = bitarray.bitarray(key)
        if LOG:
            print(f'Message: {message}')
            print(f'Message bits: {message_bits.to01()}')
            print(f'Initial key (64-bit): {key_bits.to01()}')

        # apply initial permutation
        message_bits = permutation(message_bits, INITIAL_PERMUTATION)
        if LOG:
            print(f'Message after initial permutation (IP): {message_bits.to01()}')

        # generate round keys
        keys = generate_keys(key_bits)

        # init cipher
        cipher_bits = message_bits

        # perform 16 iterations of encryption process
        for i in range(16):
            cipher_bits = des_round(cipher_bits, keys[i], i)

        # swap c_l and c_r
        cipher_bits = cipher_bits[32:] + cipher_bits[:32]
        if LOG:
            print(f'Cipher after final swap: {cipher_bits.to01()}')

        # apply final permutation
        cipher_bits = permutation(cipher_bits, FINAL_PERMUTATION)
        if LOG:
            print(f'Cipher after final permutation (IP^-1): {cipher_bits.to01()}')

        return {
            'cipher': cipher_bits.to01()
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
            message: String (8-character plaintext string)
        """
        # request body
        req_json = request.get_json(force=True)
        cipher = req_json['cipher']
        key = req_json['key']

        # convert message and key to bit arrays
        cipher_bits = bitarray.bitarray(cipher)
        key_bits = bitarray.bitarray(key)
        if LOG:
            print(f'Cipher: {cipher_bits.to01()}')
            print(f'Initial key (64-bit): {key_bits.to01()}')

        # apply initial permutation
        cipher_bits = permutation(cipher_bits, INITIAL_PERMUTATION)
        if LOG:
            print(f'Cipher after initial permutation (IP): {cipher_bits.to01()}')

        # generate round keys
        keys = generate_keys(key_bits)

        # perform 16 iterations of reversed encryption process
        for i in reversed(range(16)):
            cipher_bits = des_round(cipher_bits, keys[i], i)

        # swap c_l and c_r
        cipher_bits = cipher_bits[32:] + cipher_bits[:32]
        if LOG:
            print(f'Cipher after final swap: {cipher_bits.to01()}')

        # apply final permutation
        cipher_bits = permutation(cipher_bits, FINAL_PERMUTATION)
        if LOG:
            print(f'Cipher after final permutation (IP^-1): {cipher_bits.to01()}')

        try:
            return {
                'message': cipher_bits.tobytes().decode('utf-8')
            }, 200
        except UnicodeDecodeError:
            return {
                'error': 'Invalid cipher-key pair.'
            }, 400


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
    # command-line args
    parser = argparse.ArgumentParser()
    parser.add_argument('-log', action='store_true')
    args = parser.parse_args()

    # check for log flag
    if args.log:
        LOG = True

    app.run(host='127.0.0.1', debug=True)
