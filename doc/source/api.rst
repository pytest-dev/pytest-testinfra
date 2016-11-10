API
===

.. _connection api:

Connection API
~~~~~~~~~~~~~~

You can use testinfra outside of pytest or you can dynamically get a
connection and call fonction from modules::

    >>> import testinfra
    >>> conn = testinfra.get_backend("paramiko://root@server:2222", sudo=True)
    >>> conn.File("/etc/shadow").mode == 0o640
    True

Same applies to all :ref:`modules`.

For instance you could make a test to compare two files on two different servers::

    import testinfra

    def test_same_passwd():
        a = testinfra.get_backend("ssh://a")
        b = testinfra.get_backend("ssh://b")
        assert a.File("/etc/passwd").content == a.File("/etc/passwd").content
