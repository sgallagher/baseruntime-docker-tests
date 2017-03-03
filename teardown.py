#!/usr/bin/env python

import os
import subprocess
import re

from avocado import main
from avocado import Test


class BaseRuntimeTeardownDocker(Test):

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

    def testRemoveDockerImage(self):

        # Clean-up old test artifacts (docker containers, image, mock root)

        docker_containerlist_cmdline = 'docker ps --filter=ancestor=base-runtime-smoke -a -q'
        try:
            containerlist = subprocess.check_output(docker_containerlist_cmdline,
                stderr = subprocess.STDOUT, shell = True)
        except subprocess.CalledProcessError as e:
            self.error("command '%s' returned exit status %d; output:\n%s" %
                (e.cmd, e.returncode, e.output))
        else:
            self.log.info("docker container list with '%s' succeeded with output:\n%s" %
                (docker_containerlist_cmdline, containerlist))

        if containerlist:
            containers = re.sub('[\r\n]+', ' ', containerlist)
            self.log.info("docker containers using image base-runtime-smoke need to be removed: %s\n" %
                containers);
            docker_teardown_cmdline = 'docker rm %s' % containers
            try:
                docker_teardown_output = subprocess.check_output(docker_teardown_cmdline,
                    stderr = subprocess.STDOUT, shell = True)
            except subprocess.CalledProcessError as e:
                self.error("command '%s' returned exit status %d; output:\n%s" %
                    (e.cmd, e.returncode, e.output))
            else:
                self.log.info("docker container teardown with '%s' succeeded with output:\n%s" %
                    (docker_teardown_cmdline, docker_teardown_output))
        else:
            self.log.info("no docker containers are using image base-runtime-smoke\n")

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





