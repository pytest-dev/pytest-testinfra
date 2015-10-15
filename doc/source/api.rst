API
===

.. _connection api:

Connection API
~~~~~~~~~~~~~~

You can use testinfra outside of pytest or you can dynamically get a
connection and call fonction from modules::

    >>> import testinfra
    >>> conn = testinfra.get_backend("paramiko://root@server:2222", sudo=True)
    >>> File = conn.get_module("File")
    >>> File("/etc/shadow").mode == 0o640
    True

Same applies to all :ref:`modules`.

For instance you could make a test to compare two files on two different servers::

    import testinfra

    def test_same_passwd():
        FileA = testinfra.get_backend("ssh://a").get_module("File")
        FileB = testinfra.get_backend("ssh://b").get_module("File")
        assert FileA("/etc/passwd").content == FileB("/etc/passwd").content
