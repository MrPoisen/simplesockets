# Introduction  
There are two modules in securesockets: PyCryptodome_Socket and SelfmadeCipher_Socket.  
The PyCryptodome_Socket module requires [pycryptodome](https://pypi.org/project/pycryptodome/). 
The SelfmadeCipher_Socket module does not require any dependencies. Unfortunately, there are still some errors which haven't 
been fixed yet. Therefore, you should use the PyCryptodome Variant.

The use of the SelfmadeCipher_Socket module is <span style="color:firebrick"> ***not*** </span> recommended. For real 
secure communication, use the Pycryptodome variant.  
Both variants already contain an `on_connect` function. The Server already contains an `on_disconnect` function.  
