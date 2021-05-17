from multiprocessing import Queue, Process
from time import time
from hashlib import md5
import socket
from threading import Thread

IN_FILE = 'test.txt'
OUT_FILE = 'out2.txt'
PASSWORD = '1234567'

CHUNK_SIZE = 5000       # how many bytes in single data chunk
METADATA_SIZE = 50      # how many bytes in metadata
HOST = '127.0.0.1'      # socket host to bind
PORT = 9999             # socket port to bind
MAX_CLIENTS = 10        # max allowed clients


class EncryptionWorker:
    def __init__(self, input_file, output_file, password):
        self.input_file = input_file
        self.output_file = output_file

        self.working_thread = []

        self.password = password
        self.password_digest = md5(self.password.encode()).hexdigest()

        self.done = False

        self.input_queue = Queue()
        self.output_queue = Queue()

        self.reader_proc = Process(target=self.read_from_file)
        self.writer_proc = Process(target=self.write_to_file)

        self.reader_proc.start()
        self.writer_proc.start()

    def read_from_file(self):
        read_idx = 0
        with open(self.input_file, 'rb') as f:
            while True:
                line = f.read(CHUNK_SIZE)
                if len(line) == 0:
                    break
                self.input_queue.put((read_idx, bytearray(line)))
                read_idx += 1

    def write_to_file(self):
        buffer = {}
        curr_idx = 0

        with open(self.output_file, 'wb') as f:
            try:
                for idx, result in iter(self.output_queue.get, 'STOP'):
                    if curr_idx != idx:
                        # save to buffer
                        buffer[idx] = result
                    else:
                        f.write(result)
                        curr_idx += 1

                    # check buffer
                    while curr_idx in buffer:
                        f.write(buffer[curr_idx])
                        buffer.pop(curr_idx)
                        curr_idx += 1
            except KeyboardInterrupt:
                print('Queue interrupted...')

    def add_new_connection(self, conn):
        print(f'Connection from {conn.getpeername()} accepted')
        th = Thread(target=self.handle_connection, args=(conn,))
        self.working_thread.append(th)
        th.start()

    def handle_connection(self, conn):
        while self.done is False:
            # wait for ready flag from client
            data = conn.recv(METADATA_SIZE)

            # all data computed, end connection
            if 'STOP' in data.decode():
                self.done = True
                break

            # abnormal flow
            if 'READY' not in data.decode():
                raise ValueError('Wrong data flow!')

            # queue is empty, no more data to process, inform client
            if self.input_queue.empty() is True:
                conn.send(b'STOP')
                continue

            index, data = self.input_queue.get()

            # send data to process
            conn.send(str(index).zfill(10).encode() + self.password_digest.encode() + data)

            # receive results and store them in output queue
            data = conn.recv(CHUNK_SIZE + METADATA_SIZE)
            data_index = int(data[:10].decode())
            data = data[10:]
            self.output_queue.put((data_index, data))

            # confirm receiving results
            conn.sendall(b'ACK')

        print(f'Connection with {conn.getpeername()} closed.')
        conn.sendall(b'STOP')
        conn.recv(METADATA_SIZE)
        conn.close()


if __name__ == '__main__':
    enc_worker = EncryptionWorker(IN_FILE, OUT_FILE, PASSWORD)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    print(f'Socket bound to {HOST}:{PORT}')

    s.listen(MAX_CLIENTS)
    print("Listening started...")

    start_time = None
    while enc_worker.done is False:
        try:
            conn, addr = s.accept()

            # start timing only after first connection was established
            start_time = start_time or time()
        except KeyboardInterrupt:
            if 'conn' in locals():
                conn.close()
            print('Operation interrupted...')
            break

        enc_worker.add_new_connection(conn)

    s.close()

    # finish writing to file
    enc_worker.output_queue.put('STOP')
    enc_worker.writer_proc.join()
    print(f'\nEncryption/decryption finished in {time() - start_time}')
