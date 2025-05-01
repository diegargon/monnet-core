import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


class EncryptService:
    def __init__(self, private_key_path: str = "/etc/monnet/certs-priv/monnet_private_key.pem",
                 public_key_path: str = "/etc/monnet/certs-pub/monnet_public_key.pem"):
        self.private_key_path = Path(private_key_path)
        self.public_key_path = Path(public_key_path)

        if not self.private_key_path.exists() or not self.public_key_path.exists():
            raise FileNotFoundError("Private or public key file not found. Ensure keys are generated and installed.")

        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()

    def _load_private_key(self):
        with open(self.private_key_path, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )

    def _load_public_key(self):
        with open(self.public_key_path, "rb") as key_file:
            return serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )

    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypts a plaintext string using the public key.
        :param plaintext: The string to encrypt.
        :return: Encrypted data as bytes.
        """
        if not plaintext:
            raise ValueError("Plaintext cannot be empty.")
        return self.public_key.encrypt(
            plaintext.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypts ciphertext using the private key.

        Use PKCS1v15 for compatibility with the PHP frontend:
            openssl_public_encrypt
            RSA_PKCS1_PADDING

        :param ciphertext: The encrypted data as bytes.
        :return: Decrypted plaintext string.
        """
        if not ciphertext:
            raise ValueError("Ciphertext cannot be empty.")
        return self.private_key.decrypt(
            ciphertext,
            padding.PKCS1v15()
        ).decode()
