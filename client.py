import socket
import sys
from multiprocessing import Process
from config import CHUNK_SIZE, METADATA_SIZE, NO_LOOPS, PORT, PROCESSES

HOST = '127.0.0.1'  # The server's hostname or IP address


def encrypt(chunk, password, loop_size=NO_LOOPS):
    digest_bytes = bytes(password.encode())
    digest_len = len(digest_bytes)

    chunk_len = len(chunk)
    for loop_idx in range(loop_size):
        for i in range(chunk_len):
            chunk[(i+loop_idx) % chunk_len] = chunk[(i+loop_idx) % chunk_len] ^ digest_bytes[i % digest_len]

    return chunk


def handle_conn(proc_index):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f'(Process: {proc_index+1}) Connected to {HOST}:{PORT}')

        while True:
            # send ready flag
            s.sendall(b'READY')

            # wait for data to process
            data = s.recv(CHUNK_SIZE + METADATA_SIZE)

            # check if enough data was received
            if len(data) < 10:
                break

            # extract index, password and data to process
            index = data[:10]
            password = data[10:42].decode()
            data = data[42:]
            result = encrypt(bytearray(data), password)

            # send back results
            s.sendall(index + result)

            # wait for confirmation of receiving result
            s.recv(METADATA_SIZE)


def client_conn(proc_index):
    try:
        handle_conn(proc_index)
    except ConnectionRefusedError:
        print('Connection closed!')
    except BrokenPipeError:
        print('Broken pipe, connection was closed earlier!')
    except ConnectionResetError:
        print('Connection resetted!')


if __name__ == '__main__':
    # check script arguments
    if len(sys.argv) > 1:
        CHUNK_SIZE = int(sys.argv[1])
        NO_LOOPS = int(sys.argv[2])
        PROCESSES = int(sys.argv[3])

    processes = []
    for idx in range(PROCESSES):
        proc = Process(target=client_conn, args=(idx,))
        processes.append(proc)
        proc.start()

    for proc in processes:
        proc.join()
