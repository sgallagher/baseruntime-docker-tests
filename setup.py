#!/usr/bin/env python

import os
import subprocess
import re

from avocado import main
from avocado import Test


class BaseRuntimeSetupDocker(Test):

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

    def testCreateDockerImage(self):

        # Clean-up any old test artifacts (docker image, mock root) first:

        docker_teardown_cmdline = 'docker rmi base-runtime-smoke'
        try:
            docker_teardown_output = subprocess.check_output(docker_teardown_cmdline,
                stderr = subprocess.STDOUT, shell = True)
        except subprocess.CalledProcessError as e:
            if "No such image" not in e.output:
                self.error("command '%s' returned exit status %d; output:\n%s" %
                    (e.cmd, e.returncode, e.output))
            else:
                self.log.info("No existing docker image named base-runtime-smoke")
        else:
            self.log.info("docker teardown with '%s' succeeded with output:\n%s" %
                (docker_teardown_cmdline, docker_teardown_output))

        mock_teardown_cmdline = ['mock', '-r', self.mockcfg, '--scrub=all']
        try:
            mock_teardown_output = subprocess.check_output(mock_teardown_cmdline,
                stderr = subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.error("command '%s' returned exit status %d; output:\n%s" %
                (e.cmd, e.returncode, e.output))
        self.log.info("mock teardown with '%s' succeeded with output:\n%s" %
            (mock_teardown_cmdline, mock_teardown_output))

        # Initialize chroot with mock
        mock_cmdline = ['mock', '-r', self.mockcfg, 'init']
        try:
            mock_output = subprocess.check_output(mock_cmdline,
                stderr = subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.error("command '%s' returned exit status %d; output:\n%s" %
                (' '.join(e.cmd), e.returncode, e.output))

        self.log.info("command  '%s' succeeded with output:\n%s" %
            (' '.join(mock_cmdline), mock_output))

        # Import it as a docker image
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

if __name__ == "__main__":
    main()
