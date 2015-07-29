import pytest

@pytest.fixture(scope="module")
def disabled_functions(Command):
    # get disable_function from php.ini
    disabled_functions = set()
    output = Command.check_output(
        "grep '^disable_functions\s*=' /etc/php5/fpm/php.ini"
    )
    for function in output.split("=", 1)[1].split(","):
        disabled_functions.add(function.strip())

    return disabled_functions


@pytest.mark.parametrize("func_name", [
    "show_source", "shell_exec", "popen", "proc_open",
    "passthru", "exec", "eval", "proc_terminate", "system",
    "parse_ini_file", "pcntl_alarm", "pcntl_fork",
    "pcntl_waitpid", "pcntl_wait", "pcntl_wifexited",
    "pcntl_wifstopped", "pcntl_wifsignaled", "pcntl_wexitstatus",
    "pcntl_wtermsig", "pcntl_wstopsig", "pcntl_signal",
    "pcntl_signal_dispatch", "pcntl_get_last_error",
    "pcntl_strerror", "pcntl_sigprocmask", "pcntl_sigwaitinfo",
    "pcntl_sigtimedwait", "pcntl_exec", "pcntl_getpriority",
    "pcntl_setpriority", "curl_exec", "curl_milti_exec",
])
def test_php_disable_functions(disabled_functions, func_name):
    assert func_name in disabled_functions
