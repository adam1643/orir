from multiprocessing import Queue, Process, cpu_count
from time import time
from hashlib import md5

PROCESSES = cpu_count()
CHUNK_SIZE = 5000              # how many bytes in single data chunk
NO_LOOPS = 50                  # how many encryption loops


class EncryptionWorker:
    def __init__(self, no_proc, input_file, output_file, password, oper_type='encrypt'):
        self.no_proc = no_proc
        self.input_file = input_file
        self.output_file = output_file

        self.password = password
        self.loop_size = NO_LOOPS

        self.input_queue = Queue()
        self.output_queue = Queue()
        if oper_type == 'encrypt':
            self.encryption = True
        elif oper_type == 'decrypt':
            self.encryption = False
        else:
            raise ValueError('Wrong operation type!')

        self.reader_proc = Process(target=self.read_from_file)
        self.writer_proc = Process(target=self.write_to_file)
        if self.encryption is True:
            self.workers = [Process(target=self.encrypt_data) for _ in range(self.no_proc)]
        else:
            self.workers = [Process(target=self.decrypt_data) for _ in range(self.no_proc)]

        start = time()
        self.reader_proc.start()
        self.writer_proc.start()
        for worker in self.workers:
            worker.start()

        self.reader_proc.join()
        self.writer_proc.join()

        print(f'({self.no_proc}) time elapsed: {time()-start}')

    def read_from_file(self):
        idx = 0
        with open(self.input_file, 'rb') as f:
            while True:
                line = f.read(CHUNK_SIZE)
                if len(line) == 0:
                    break
                self.input_queue.put((idx, bytearray(line)))
                idx += 1

        for _ in range(self.no_proc):
            self.input_queue.put('STOP')

    def write_to_file(self):
        buffer = {}
        curr_idx = 0

        with open(self.output_file, 'wb') as f:
            for _ in range(self.no_proc):
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

    def encrypt(self, chunk, chunk_index):
        digest = md5(bytes(self.password.encode())).hexdigest()
        digest_bytes = bytes(digest.encode())
        digest_len = len(digest_bytes)

        chunk_len = len(chunk)
        for loop_idx in range(self.loop_size):
            for i in range(chunk_len):
                chunk[(i+loop_idx) % chunk_len] = chunk[(i+loop_idx) % chunk_len] ^ digest_bytes[i % digest_len]

        self.output_queue.put((chunk_index, chunk))

    def decrypt(self, chunk, chunk_index):
        digest = md5(bytes(self.password.encode())).hexdigest()
        digest_bytes = bytes(digest.encode())
        digest_len = len(digest_bytes)

        chunk_len = len(chunk)
        for loop_idx in range(self.loop_size):
            for i in range(chunk_len):
                chunk[(i+(self.loop_size-1-loop_idx)) % chunk_len] = chunk[(i+(self.loop_size-1-loop_idx)) % chunk_len] ^ digest_bytes[i % digest_len]

        self.output_queue.put((chunk_index, chunk))

    def encrypt_data(self):
        for idx, chunk in iter(self.input_queue.get, 'STOP'):
            self.encrypt(chunk, idx)

        self.output_queue.put('STOP')

    def decrypt_data(self):
        for idx, chunk in iter(self.input_queue.get, 'STOP'):
            self.decrypt(chunk, idx)

        self.output_queue.put('STOP')


if __name__ == '__main__':
    # try for different number of processes
    for proc in range(PROCESSES):
        enc_worker = EncryptionWorker(proc+1, 'test.txt', 'out2.txt', 'asdjhkasjkdhaskjd')
        # enc_worker2 = EncryptionWorker(proc+1, 'out.txt', 'in2.txt', 'asdjhkasjkdhaskjd')
