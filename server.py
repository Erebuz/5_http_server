
import socket
import threading
import os

# Конфигурация сервера
HOST = 'localhost'
PORT = 8080
DOCUMENT_ROOT = './www'  # Корневая папка для статических файлов

# Функция для обработки клиентских запросов
def handle_request(client_socket):
    try:
        request = client_socket.recv(1024).decode('utf-8')
        if not request:
            return

        headers = request.split('\n')
        method, path, _ = headers[0].split()

        if method not in ['GET', 'HEAD']:
            response = 'HTTP/1.1 405 Method Not Allowed\n\nMethod Not Allowed'
            client_socket.sendall(response.encode('utf-8'))
            return

        # Удаление начального символа '/'
        if path == '/':
            path = '/index.html'
        
        file_path = DOCUMENT_ROOT + path

        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                body = file.read()
            response_headers = 'HTTP/1.1 200 OK\n'
            response_headers += f'Content-Length: {len(body)}\n'
            response_headers += 'Content-Type: text/html\n\n'
            response = response_headers.encode('utf-8')

            if method == 'GET':
                response += body
        else:
            response = 'HTTP/1.1 404 Not Found\n\n404 Not Found'.encode('utf-8')

        client_socket.sendall(response)
    finally:
        client_socket.close()


def handle_client(conn_sock: socket.socket) -> None:
    print('REQUEST:', conn_sock.getsockname())

    handler = threading.Thread(target=handle_request, args=(conn_sock,))
    handler.start()

# Функция для запуска сервера
def start_server():
    listening_socket = socket.create_server(
        (HOST, PORT),
        family=socket.AF_INET,
        backlog=5,
    )

    with listening_socket:
        print('Server started on:', HOST, PORT)
        while True:
            connected_socket, client_addr = listening_socket.accept()

            handle_client(connected_socket)


if __name__ == '__main__':
    start_server()
