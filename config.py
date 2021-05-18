IN_FILE = 'out.txt'
OUT_FILE = 'orig.txt'
PASSWORD = '1234567'

LOG_FILE = 'log.txt'

PROCESSES = 8
CHUNK_SIZE = 5000       # how many bytes in single data chunk
METADATA_SIZE = 50      # how many bytes in metadata
NO_LOOPS = 50           # how many encryption loops

PORT = 9999             # socket port to bind
MAX_CLIENTS = 10        # max allowed clients


def log_data(data):
    with open(LOG_FILE, 'a') as f:
        f.write(data)
        f.write('\n')
