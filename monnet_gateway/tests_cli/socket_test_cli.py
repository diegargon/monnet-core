"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Socket CLI test

"""

from monnet_gateway.networking.socket import SocketHandler

def main():
    # Crear un contexto simulado
    class MockContext:
        def get_logger(self):
            import logging
            logging.basicConfig(level=logging.DEBUG)
            return logging.getLogger("SocketHandlerTest")

    # Crear instancia de SocketHandler
    socket_handler = SocketHandler(timeout=5.0)

    print("=== Probando SocketHandler ===")

    # Probar creación de socket TCP
    print("\n[1] Creando socket TCP...")
    if socket_handler.create_tcp_socket():
        print("Socket TCP creado exitosamente.")
    else:
        print("Error al crear socket TCP.")
        return

    # Probar bind y listen en modo servidor TCP
    print("\n[2] Enlazando socket TCP al puerto 12345...")
    if socket_handler.bind("127.0.0.1", 12345):
        print("Socket TCP enlazado exitosamente.")
    else:
        print("Error al enlazar socket TCP.")
        return

    print("\n[3] Poniendo socket TCP en modo escucha...")
    if socket_handler.tcp_listen():
        print("Socket TCP en modo escucha.")
    else:
        print("Error al poner socket TCP en modo escucha.")
        return

    # Probar creación de socket UDP
    print("\n[4] Creando socket UDP...")
    if socket_handler.create_udp_socket():
        print("Socket UDP creado exitosamente.")
    else:
        print("Error al crear socket UDP.")
        return

    # Probar bind en modo UDP
    print("\n[5] Enlazando socket UDP al puerto 12346...")
    if socket_handler.bind("127.0.0.1", 12346):
        print("Socket UDP enlazado exitosamente.")
    else:
        print("Error al enlazar socket UDP.")
        return

    # Probar envío y recepción de datos en UDP
    print("\n[6] Probando envío y recepción de datos en UDP...")
    try:
        # Enviar datos a través del socket UDP
        data_to_send = b"Hola desde UDP"
        destination = ("127.0.0.1", 12346)
        if socket_handler.send(data_to_send, destination):
            print(f"Datos enviados a {destination}: {data_to_send}")
        else:
            print("Error al enviar datos en UDP.")

        # Recibir datos en el socket UDP
        received_data, address = socket_handler.receive()
        if received_data:
            print(f"Datos recibidos de {address}: {received_data}")
        else:
            print("No se recibieron datos en UDP.")
    except Exception as e:
        print(f"Error durante la prueba de UDP: {e}")

    print("\n[7] Cerrando sockets...")
    socket_handler.close()
    print("Sockets cerrados.")

if __name__ == "__main__":
    main()