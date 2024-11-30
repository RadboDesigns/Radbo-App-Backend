import base64
import string
import random
import hashlib
from Crypto.Cipher import AES

class PaytmChecksum:
    @staticmethod
    def generate_checksum(param_dict, merchant_key):
        # Get sorted list of dictionary elements
        params_string = PaytmChecksum.get_sorted_params_string(param_dict)
        
        # Generate checksum
        return PaytmChecksum.encrypt(params_string, merchant_key)

    @staticmethod
    def verify_checksum(param_dict, merchant_key, checksum):
        # Get sorted list of dictionary elements
        params_string = PaytmChecksum.get_sorted_params_string(param_dict)
        
        # Decrypt checksum
        return checksum == PaytmChecksum.encrypt(params_string, merchant_key)

    @staticmethod
    def get_sorted_params_string(params):
        sorted_params = sorted(params.items(), key=lambda x: x[0].lower())
        params_string = map(lambda x: str(x[0]) + "=" + str(x[1]), sorted_params)
        return '|'.join(params_string)

    @staticmethod
    def encrypt(input_string, key):
        iv = '@@@@&&&&####$$$$'
        input_string = PaytmChecksum.pad_input(input_string)
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
        encrypted = cipher.encrypt(input_string.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def pad_input(data):
        block_size = 16
        remainder = len(data) % block_size
        padding_needed = block_size - remainder
        return data + chr(padding_needed) * padding_needed