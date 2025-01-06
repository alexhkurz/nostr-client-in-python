# generate_keys.py
# 
import json
from secp256k1 import PrivateKey, PublicKey

def generate_key_pair():
    private_key = PrivateKey()
    public_key = private_key.pubkey

    priv_hex = private_key.private_key.hex()
    pub_hex = public_key.serialize()[1:33].hex()

    print(priv_hex); print(len(priv_hex))
    print(pub_hex); print(len(pub_hex))

    return priv_hex, pub_hex

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
