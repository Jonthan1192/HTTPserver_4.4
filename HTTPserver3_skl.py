# https://github.com/Jonthan1192/HTTPserver_4.4.git

import os
import socket
import threading

exts_txt = ['.js', '.txt', '.css']
exts_bin = ['.html', '.jpg', '.gif', '.ico']

moved_302 = {r'duck.jpg': r'webroot\imgs\duck.jpg', r'aaa.jpg': r'webroot\imgs\aaa.jpg'}

local_path = r'E:\Ex4.4\HTTPserver_Ex4.4\\'

exit_all = False

PROTOCOL = 'HTTP1.1'

debug_prints = True

lock = threading.Lock()


def safe_prints(to_print):
    global lock
    lock.acquire()
    print(to_print)
    lock.release()


def http_send(s, reply_header, reply_body, tid):
    global debug_prints
    reply = reply_header.encode()
    if reply_body != '':
        try:
            body_length = len(reply_body)
            reply_header += 'Content-Length: ' + str(body_length) + '\r\n' + '\r\n'
            reply = reply_header.encode() + reply_body
        except Exception as e:
            safe_prints(e)
    else:
        reply += b'\r\n'
    s.send(reply)
    global debug_prints
    if debug_prints:
        to_print = f'SENT: {(reply[:min(200, len(reply))] + b",")} to client number {tid}'
        safe_prints(to_print)


def http_recv(sock, tid, block_size=8192):
    global debug_prints
    byte_data = sock.recv(block_size)
    try:
        first_row = byte_data[:byte_data.find(b"\r\n")]
        first_row = first_row.split(b" ")
        if len(first_row) != 3 or first_row[0] != b"GET" or first_row[2] != b"HTTP/1.1":
            return b'', b''
        header_body_list = byte_data.split(b"\r\n\r\n")
        header = header_body_list[0].decode()
        body = header_body_list[1].decode()
        if debug_prints:
            to_print = f"RECEIVED:" + f"{byte_data[:min(200, len(byte_data))]}, from client number {tid}"
            safe_prints(to_print)
        return header, body
    except Exception as err:
        safe_prints(err)
        return b'', b''


def get_type_header(file_path):
    file_path = file_path[::-1]
    file_path = file_path[:file_path.find('.')]
    file_path = file_path[::-1]
    return file_path


def get_file_data(requested_file):
    global local_path
    if not os.path.exists(requested_file):
        return b""
    with open(local_path + requested_file, "rb") as f:
        file_data = f.read()
    return file_data


def handle_request(request_header, body):
    global moved_302
    header_parts = request_header.split(" ")
    url = header_parts[1]
    parameters = []
    if url.find('?') != -1:
        file_path = url[1:url.find('?')]
        parameters = url[url.find('?') + 1:].split('?')
    else:
        file_path = url[1:]
    file_path = file_path.replace("/", "\\")
    reply_header = "HTTP/1.1 200 OK\r\n"
    if file_path == "calculate-next" or file_path == r"webroot\calculate-next":
        num = parameters[0][4:]
        if not num.isnumeric():
            reply_header, reply_body = "HTTP/1.1 404 Not Found\r\n", b''
            return reply_header, reply_body
        num = int(num) + 1
        num = str(num).encode()
        reply_body = num
        reply_header += 'Content-Type: text/plain\r\n'
        return reply_header, reply_body
    elif file_path == "":
        file_path = r"webroot\\index.html"
    elif file_path in moved_302.keys():
        new_path = moved_302[file_path]
        reply_header, reply_body = f"HTTP/1.1 302 Moved Temporarily\r\nLocation: {new_path}\r\n", b''
        return reply_header, reply_body
    elif file_path == r"systemFiles\NotFound.html" or file_path == r"systemFiles\AccessDenied.html":
        reply_header, reply_body = "HTTP/1.1 403 Forbidden\r\n", b''
        return reply_header, reply_body

    reply_body = get_file_data(file_path)
    if reply_body == b"":
        reply_header = "HTTP/1.1 404 Not Found\r\n"
        return reply_header, reply_body
    file_type = get_type_header(file_path)
    if file_type == "txt" or file_type == "html":
        reply_header += 'Content-Type: text/html; charset=UTF-8\r\n'
    elif file_type == "jpg" or file_type == "jpeg" or file_type == "ico":
        reply_header += 'Content-Type: image/jpeg\r\n'
    elif file_type == "js":
        reply_header += 'Content-Type: text/javascript; charset=UTF-8\r\n'
    elif file_type == "css":
        reply_header += 'Content-Type: text/css\r\n'
    return reply_header, reply_body


def handle_client(s_clint_sock, tid, addr):
    global exit_all
    to_print = f'new client arrive {tid} {addr}'
    safe_prints(to_print)
    while not exit_all:
        request_header, request_body = http_recv(s_clint_sock, tid)
        if request_header == b'':
            reply_header, reply_body = "HTTP/1.1 500 Internal Server Error\r\n", b''
        else:
            reply_header, reply_body = handle_request(request_header, request_body)
        if PROTOCOL == "HTTP1.0":
            reply_header += "Connection': close\r\n"
        else:
            reply_header += "Connection: keep-alive\r\n"
        http_send(s_clint_sock, reply_header, reply_body, tid)
        if PROTOCOL == "HTTP1.0":
            break
    to_print = f"Client {tid} Closing"
    safe_prints(to_print)
    s_clint_sock.close()


def main():
    global exit_all
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 80))
    server_socket.listen(5)
    threads = []
    tid = 1
    while True:
        try:
            # print('\nbefore accept...')
            client_socket, addr = server_socket.accept()
            t = threading.Thread(target=handle_client, args=(client_socket, tid, addr))
            t.start()
            threads.append(t)
            tid += 1
        except socket.error as err:
            print('socket error', err)
            break
    exit_all = True
    for t in threads:
        t.join()

    server_socket.close()
    print('server will die now')


if __name__ == "__main__":
    main()
