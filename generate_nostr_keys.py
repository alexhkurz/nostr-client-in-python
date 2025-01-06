import json
from ecdsa import SigningKey, SECP256k1

def generate_key_pair():
    # Generate a private key
    private_key = SigningKey.generate(curve=SECP256k1)
    
    # Derive the public key
    public_key = private_key.get_verifying_key()
    
    # Convert keys to hexadecimal strings
    private_key_hex = private_key.to_string().hex()
    public_key_hex = public_key.to_string("compressed").hex()
    
    return private_key_hex, public_key_hex

def set_keys(state, private_key=None, public_key=None):
    if not private_key and not public_key:
        private_key, public_key = generate_key_pair()

    state['private_key'] = private_key
    state['public_key'] = public_key

def save_keys_to_file(state, filename='config2.json'):
    with open(filename, 'w') as file:
        json.dump(state, file, indent=4)
    print(f"Keys saved to {filename}")

# Example usage
state = {}
set_keys(state)
save_keys_to_file(state)
