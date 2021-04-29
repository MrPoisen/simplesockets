# Roadmap: 
- bugfixes
- more usability
- better documentation of the code

## Release 0.0.9:

- improved code documentation
- improved documentation
- small changes

## Release 0.0.8:

- added `await_event(timeout=0)` function to the Client and Server
- added documentation to the code
- added `Address` property to the Client
- added `SetupError`
- changed Project build  
- bugfixes

## Release 0.0.7:

- ``autorecv()`` now can toggle the autorecv thread
- ``Server.killed()`` is now a property
- added a disconnect function to the Client  
- added Address property to the Client  
- added own exceptions
- fixed own encryption  
- small changes

## Release 0.0.6:

- made all threads daemon 
- made `users_key` public, added `connected_users` property
- bugfixes
- small changes
- removed the ``exit()`` functions
- added documentation to the code

## Release 0.0.5:

- added `__str__()` and `__repr__()` 
- added own RSA and Vigeneré for semi secure encryption without dependencies.
- added new Client and Server class with own RSA encryption and Vigeneré.
- ``on_receive`` on the Server takes now 3 arguments: client_socket, address, recved
- added ``decrypt_data()`` function to the Secure Servers

## Release 0.0.4:

- fixed imports
- added more typehints

## Release 0.0.3:

- added `on_connect`, `on_disconnect` and `on_receive` functions
- changes to the `exit()` function
- bugfixes
- added hash functions in the cipher module
- securesockets is now a package containing `S_Client` and `S_Server`
- new event variable containing events and exceptions
- added ipv6 versions to S_Client and S_Server (untested).  

## Release 0.0.2:

- created ipv6 versions

## Release 0.0.1:

- created TCPServer
- created TCPClient
- created TCPServer_secure
- created TCPClient_secure