#!/usr/bin/env python

import os
import subprocess
import re

from avocado import main
from avocado import Test

import cleanup
import brtconfig


class BaseRuntimeTeardownDocker(Test):

    def setUp(self):

        self.mockcfg = brtconfig.get_mockcfg(self)
        self.br_image_name = brtconfig.get_docker_image_name(self)

    def testRemoveDockerImage(self):

        # Clean-up old test artifacts (docker containers, image, mock root)
        try:
            cleanup.cleanup_docker_and_mock(self.mockcfg, self.br_image_name)
        except:
            self.error("artifact cleanup failed")
        else:
            self.log.info("artifact cleanup successful")

if __name__ == "__main__":
    main()
