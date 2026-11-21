import rsa

def generate_keys():
    (public_key, private_key) = rsa.newkeys(2048)
    
    with open('shared/public_key.pem', 'wb') as f:
        f.write(public_key.save_pkcs1())
    
    with open('shared/private_key.pem', 'wb') as f:
        f.write(private_key.save_pkcs1())

def verify_signature(msg, signature):
    with open('shared/public_key.pem', 'rb') as f:
        loaded_public_key = rsa.PublicKey.load_pkcs1(f.read())

    try:
        rsa.verify(msg.encode(), bytes.fromhex(signature), loaded_public_key)
        return True
    except rsa.VerificationError:
        return False

def sign_message(msg):
    with open('shared/private_key.pem', 'rb') as f:
        loaded_private_key = rsa.PrivateKey.load_pkcs1(f.read())

    signature = rsa.sign(msg.encode(), loaded_private_key, 'SHA-256')

    return signature
