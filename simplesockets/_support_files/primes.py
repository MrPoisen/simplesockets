import json

def get_primes(n: int) -> list:
    primes = [3]
    number_primes = 1
    current_number = 4
    while n > number_primes:
        for pr in primes:
            if pow(current_number, 1, pr) == 0:
                break
        else:
            primes.append(current_number)
            number_primes += 1
        current_number += 1
    return primes

def add_primes(n: int) -> list:
    with open('primes.json', 'r') as read:
        primes = json.load(read)

    number_primes = 0
    current_number = primes[-1] + 1
    while n > number_primes:
        for pr in primes:
            if pow(current_number, 1, pr) == 0:
                break
        else:
            print("prime:", current_number)
            primes.append(current_number)
            number_primes += 1
        current_number += 1
    return primes

def remove_primes(n: int) -> list:
    with open('primes.json', 'r') as read:
        primes = json.load(read)
    return primes[:len(primes)-n]


def save_primes(primes: list):
    with open('primes.json', 'w') as write:
        json.dump(primes, write, indent=4)


def SieveOfEratosthenes(n, start: int=None):
    # https://www.geeksforgeeks.org/analysis-different-methods-find-prime-number-python/
    # Create a boolean array "prime[0..n]" and
    # initialize all entries it as true. A value
    # in prime[i] will finally be false if i is
    # Not a prime, else true.
    prime = [True for _ in range(n + 1)]
    primes_ = []
    p = 2
    if isinstance(start, int):
        p = start

    while (p * p <= n):

        # If prime[p] is not changed, then it is
        # a prime
        if (prime[p] == True):

            # Update all multiples of p
            for i in range(p * p, n + 1, p):
                prime[i] = False
        p += 1

    # Print all prime numbers
    for p in range(2, n):
        if prime[p]:
            primes_.append(p)
    return primes_

if __name__ == "__main__":
    save_primes(SieveOfEratosthenes(1_000_000))
    """primes = add_primes(1_000)
    save_primes(primes)"""
