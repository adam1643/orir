import random
import string
import sys

if len(sys.argv) < 2:
    FILENAME = 'test.txt'
    FILE_SIZE = 2   # in MB
else:
    FILENAME = sys.argv[1]
    FILE_SIZE = float(sys.argv[2])

with open(FILENAME, 'w') as f:
    for _ in range(int(FILE_SIZE * 1_000)):
        random_chunk = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=999))
        f.write(random_chunk + '\n')