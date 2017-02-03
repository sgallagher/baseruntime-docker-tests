#!/usr/bin/env python

import os
import subprocess
import re

from avocado import main
from avocado import Test

class BaseRuntimeSmokeTest(Test):

    def setUp(self):

        mockcfg = self.params.get('mockcfg')
        if mockcfg is None:
            self.error("mock configuration file for building docker image must be supplied")

        if not mockcfg.endswith(".cfg"):
            self.error("mock configuration file %s must have the extension '.cfg'" %
                mockcfg)

        mockcfg = str(mockcfg)
        if not os.path.isfile(mockcfg):
            self.error("mock configuration file %s does not exist" %
                mockcfg)
        self.log.info("mock configuration file: %s" % mockcfg)
        self.mockcfg = mockcfg

        mock_root = ''
        with open(mockcfg, 'r') as mock_cfgfile:
            for line in mock_cfgfile:
                if re.match("config_opts\s*\[\s*'root'\s*\]", line) is not None:
                    mock_root = line.split('=')[1].split("'")[1]
        if len(mock_root) == 0:
            self.error("mock configuration file %s does not specify mock root" %
                mockcfg)
        self.log.info("mock root: %s" % mock_root)
        self.mock_root = mock_root

    def testMockInit(self):

        mock_cmdline = ['mock', '-r', self.mockcfg, 'init']
        try:
            mock_output = subprocess.check_output(mock_cmdline,
                stderr = subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.error("command '%s' returned exit status %d; output:\n%s" %
                (' '.join(e.cmd), e.returncode, e.output))

        self.log.info("command  '%s' succeeded with output:\n%s" %
            (' '.join(mock_cmdline), mock_output))

    def testDockerImport(self):

        import_cmdline = ("tar -C /var/lib/mock/%s/root -c . | docker import - base-runtime-smoke" %
            self.mock_root)
        try:
            import_output = subprocess.check_output(import_cmdline,
                stderr = subprocess.STDOUT, shell = True)
        except subprocess.CalledProcessError as e:
            self.error("command '%s' returned exit status %d; output:\n%s" %
                (e.cmd, e.returncode, e.output))

        self.log.info("command  '%s' succeeded with output:\n%s" %
            (import_cmdline, import_output))

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
            try:
                test_output = subprocess.check_output(('docker run --rm base-runtime-smoke bash -c "%s"' %
                    test), stderr = subprocess.STDOUT, shell = True)
            except subprocess.CalledProcessError as e:
                self.error("command '%s' returned exit status %d; output:\n%s" %
                    (e.cmd, e.returncode, e.output))
            self.log.info("smoke test command  '%s' succeeded with output:\n%s" %
                (test, test_output))

        for test in smoke_fail:
            try:
                test_output = subprocess.check_output(('docker run --rm base-runtime-smoke bash -c "%s"' %
                    test), stderr = subprocess.STDOUT, shell = True)
            except subprocess.CalledProcessError as e:
                self.log.info("command '%s' returned exit status %d; output:\n%s" %
                    (e.cmd, e.returncode, e.output))
            else:
                self.error("smoke test command  '%s' succeeded unexpectedly with output:\n%s" %
                    (test, test_output))

    def tearDown(self):
        """
        Tear-down
        """

if __name__ == "__main__":
    main()
