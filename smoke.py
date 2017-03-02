#!/usr/bin/env python

import os
import subprocess
import re

from avocado import main
from avocado import Test


class BaseRuntimeSmokeTest(Test):

    def _run_docker_cmd(self, cmd):
        try:
            test_output = subprocess.check_output(('docker run --rm base-runtime-smoke bash -c "%s"' %
                cmd), stderr = subprocess.STDOUT, shell = True)
        except subprocess.CalledProcessError as e:
            return e.returncode, e.output
        return 0, test_output

    def testSmoke(self):
        """
        Run several smoke tests
        """

        # TODO: fill this "placeholder" with actual, complete, smoke tests:

        smoke_pass = [
            "echo 'Hello, World!'",
            "cat /etc/redhat-release",
            "rpm -q glibc"]

        smoke_fail = [
            "exit 1"]

        for test in smoke_pass:
            test_ret, test_output = self._run_docker_cmd(test)
            if test_ret == 0:
                self.log.info("smoke test command '%s' succeeded with output:\n%s" %
                    (test, test_output))
            else:
                self.error("command '%s' returned unexpected exit status %d; output:\n%s" %
                    (test, test_ret, test_output))


        for test in smoke_fail:
            test_ret, test_output = self._run_docker_cmd(test)
            if test_ret == 0:
                self.error("smoke test command '%s' succeeded unexpectly with output:\n%s" %
                    (test, test_output))
            else:
                self.log.info("command '%s' returned exit status %d; output:\n%s" %
                    (test, test_ret, test_output))

if __name__ == "__main__":
    main()
