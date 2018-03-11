===========================
Greylist Server for Postfix
===========================

|Build Status| |health| |docs| |translation| |pypi downloads| |pypi version| |pypi licence| |pypi wheel| |requires status|

.. image:: mongrey.png
   :align: center
   :alt: logo

Resume
======

:License: BSD
:Code: https://github.com/radical-software/mongrey
:Issues: https://github.com/radical-software/mongrey/issues
:Doc EN: http://mongrey.readthedocs.org/en/latest/
:Doc FR: http://mongrey.readthedocs.org/fr/latest/

Features
========

* Greylist Server high performance
* Backends: MongoDB, PostgreSQL, MySQL, Sqlite
* No software dependencies (except Backend);
* Configuration by Country, IP address, Network address, Email, Domain, Regex
    * For every policy filter
    * For black and white lists
* Optional filters:     
    * Relay deny control
    * Spoofing
    * Directory control DB, (SMTP, LDAP en cours..)
    * RBL
    * SPF
* WebUI (optional)
* REST API (in progress...)
* Cache with Memory or Redis

Sample installation for Mongrey Server - Sqlite Backend
=======================================================

::

    $ curl -L http://download.mongrey.io/latest/mongrey-server-sqlite > /usr/local/bin/mongrey-server
    
    $ chmod +x /usr/local/bin/mongrey-server
    
    $ /usr/local/bin/mongrey-server --version

Contributing
============

To contribute to the project, fork it on GitHub and send a pull request.

All contributions and suggestions are welcome.

.. _MongoDB: http://mongodb.org/
.. _Docker: https://www.docker.com/
.. _Ubuntu: http://www.ubuntu.com/
.. _Python: http://www.python.org/
.. _Gevent: http://www.gevent.org/
.. _Postfix: http://www.postfix.org
.. _Postfix_Policy: http://www.postfix.org/SMTPD_POLICY_README.html
.. _Coroutine: http://en.wikipedia.org/wiki/Coroutine
 
.. |Build Status| image:: https://travis-ci.org/radical-software/mongrey.svg?branch=master
   :target: https://travis-ci.org/radical-software/mongrey
   :alt: Travis Build Status
   
.. |pypi downloads| image:: https://img.shields.io/pypi/dm/mongrey.svg
    :target: https://pypi.python.org/pypi/mongrey
    :alt: Number of PyPI downloads
    
.. |pypi version| image:: https://img.shields.io/pypi/v/mongrey.svg
    :target: https://pypi.python.org/pypi/mongrey
    :alt: Latest Version

.. |pypi licence| image:: https://img.shields.io/pypi/l/mongrey.svg
    :target: https://pypi.python.org/pypi/mongrey
    :alt: License

.. |pypi wheel| image:: https://img.shields.io/pypi/wheel/mongrey.svg
    :target: https://pypi.python.org/pypi/mongrey/
    :alt: Python Wheel
        
.. |requires status| image:: https://requires.io/github/radical-software/mongrey/requirements.svg?branch=master
     :target: https://requires.io/github/radical-software/mongrey/requirements/?branch=master
     :alt: Requirements Status

.. |docs| image:: https://readthedocs.org/projects/mongrey-en/badge/?version=latest
    :target: http://mongrey.readthedocs.org/en/latest/
    :alt: Documentation Status     
    
.. |health| image:: https://landscape.io/github/radical-software/mongrey/master/landscape.svg?style=flat
   :target: https://landscape.io/github/radical-software/mongrey/master
   :alt: Code Health

.. |translation| image:: https://d322cqt584bo4o.cloudfront.net/mongrey/localized.png
   :target: https://crowdin.com/project/mongrey
   :alt: Translation

 