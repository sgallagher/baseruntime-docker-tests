#!/usr/bin/env python

import os
import subprocess
import re

from avocado import main
from avocado import Test

import cleanup


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

        cleanup.cleanup_docker_and_mock(self.mockcfg)

if __name__ == "__main__":
    main()
