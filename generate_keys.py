# generate_keys.py
import json
from ecdsa import SigningKey, SECP256k1

def generate_key_pair():
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.get_verifying_key()

    private_key_hex = private_key.to_string().hex()
    public_key_hex = public_key.to_string().hex()

    return private_key_hex, public_key_hex

def save_keys_to_config(private_key, public_key, filename='config.json'):
    config = {
        "private_key": private_key,
        "public_key": public_key
    }
    with open(filename, 'w') as config_file:
        json.dump(config, config_file, indent=4)
    print(f"Keys saved to {filename}")

if __name__ == "__main__":
    private_key, public_key = generate_key_pair()
    save_keys_to_config(private_key, public_key)
