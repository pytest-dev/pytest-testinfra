API
===

.. _connection api:

Connection API
~~~~~~~~~~~~~~

You can use testinfra outside of pytest. You can dynamically get a
`host` instance and call functions or access members of the respective modules::

    >>> import testinfra
    >>> host = testinfra.get_host("paramiko://root@server:2222", sudo=True)
    >>> host.file("/etc/shadow").mode == 0o640
    True

For instance you could make a test to compare two files on two different servers::

    import testinfra

    def test_same_passwd():
        a = testinfra.get_host("ssh://a")
        b = testinfra.get_host("ssh://b")
        assert a.file("/etc/passwd").content == b.file("/etc/passwd").content
