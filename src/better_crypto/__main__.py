import sys

from better_crypto.better_crypto import fib


if __name__ == "__main__":
    n = int(sys.argv[1])
    print(fib(n))
