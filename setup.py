import setuptools

setuptools.setup(
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    package_data={
        'primes': ['*.json']
    }
)