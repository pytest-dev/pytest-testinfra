# coding: utf-8
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import shutil
import sys
import tempfile
import time

import pytest


class NagiosReporter(object):

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = None
        self.total_time = None
        super(NagiosReporter, self).__init__()

    def pytest_sessionstart(self, session):
        self.start_time = time.time()

    def pytest_sessionfinish(self):
        self.total_time = time.time() - self.start_time

    def pytest_runtest_logreport(self, report):
        if report.passed:
            if report.when == "call":  # ignore setup/teardown
                self.passed += 1
        elif report.failed:
            self.failed += 1
        elif report.skipped:
            self.skipped += 1

    def report(self):
        if self.failed:
            status = "CRITICAL"
            ret = 2
        else:
            status = "OK"
            ret = 0

        sys.stdout.write((
            b"TESTINFRA %s - %d passed, %d failed, %d skipped in %.2f "
            b"seconds\n") % (
                status, self.passed, self.failed, self.skipped, self.total_time
            ))
        return ret


class RedirectStdStreams(object):
    # http://stackoverflow.com/questions/6796492/temporarily-redirect-stdout-stderr
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr
        self._old_stdout = None
        self._old_stderr = None
        super(RedirectStdStreams, self).__init__()

    def __enter__(self):
        self._old_stdout, self._old_stderr = sys.stdout, sys.stderr
        self._old_stdout.flush()
        self._old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush()
        self._stderr.flush()
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr


def main():
    if "--nagios" in sys.argv:
        out = tempfile.SpooledTemporaryFile()
        # Compat: In 2.7 SpooledTemporaryFile has no encoding param
        out.encoding = sys.stdout.encoding
        nagios_reporter = NagiosReporter()
        with RedirectStdStreams(stdout=out, stderr=out):
            pytest.main(plugins=[nagios_reporter])
        ret = nagios_reporter.report()
        out.seek(0)
        shutil.copyfileobj(out, sys.stdout)
        return ret
    else:
        return pytest.main()
