from monnet_gateway.services.encrypt_service import EncryptService


def main():
    # Define a test value to encrypt and decrypt
    test_value = "my_secret_value"

    encrypt_service = EncryptService()

    # Encrypt the test value
    encrypted_data = encrypt_service.encrypt(test_value)
    print("Encrypted (hex):", encrypted_data.hex())

    # Decrypt the encrypted data
    decrypted_data = encrypt_service.decrypt(encrypted_data)
    print("Decrypted:", decrypted_data)


if __name__ == "__main__":
    main()
