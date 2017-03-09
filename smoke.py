#!/usr/bin/env python

import os
import subprocess
import re

from avocado import main
from avocado import Test

class BaseRuntimeRunCmd(object):
    """
    Class to execute a command to a docker container
    """
    docker_container = None

    def _run_cmd(self, cmd):
        try:
            test_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as err:
            return err.returncode, err.output
        return 0, test_output


    def run_docker_cmd(self, cmd, rm_container=True):
        """
        Execute a docker command. By default it will create a new container
        Once the command finishes the container is removed
        """
        cmdline = 'docker run --rm base-runtime-smoke bash -c "%s"' % cmd

        if self.docker_container or not rm_container:
            #Want to execute command and leave container running
            if not self.docker_container:
                self.docker_container = self._run_br_container_background()
            cmdline = 'docker exec %s bash -c "%s"' % (self.docker_container, cmd)

        test_ret, test_output = self._run_cmd(cmdline)

        if self.docker_container and rm_container:
            self._rm_br_container(self.docker_container)
            self.docker_container = None

        return test_ret, test_output

    def _run_br_container_background(self):
        """
        Start new container and keep it running on background
        Return the new container ID
        """
        #Hack to leave container running: http://stackoverflow.com/questions/30209776/docker-container-will-automatically-stop-after-docker-run-d
        cmdline = "docker run -d base-runtime-smoke bash -c 'tail -f /dev/null'"
        test_ret, test_output = self._run_cmd(cmdline)
        if test_ret != 0:
            raise AssertionError('Could not start container')

        test_output = test_output.strip()
        if not test_output:
            raise AssertionError('Could not get container ID')

        container_ids = test_output.split('\n')
        if len(container_ids) > 1:
            raise AssertionError('Found more containers ID then expected')

        return container_ids[0]

    def _rm_br_container(self, container_id):
        """
        """
        cmdline = "docker stop %s" % container_id
        test_ret, test_output = self._run_cmd(cmdline)
        if test_ret != 0:
            raise AssertionError('Could not stop container %s' % container_id)

        cmdline = "docker rm %s" % container_id
        test_ret, test_output = self._run_cmd(cmdline)
        if test_ret != 0:
            raise AssertionError('Could not remove container %s' % container_id)

        print "INFO: Removed container %s" % container_id
        return test_ret

    #Probably not the best way, but I could not find away to guarantee container will be removed
    def __del__(self):
        if self.docker_container:
            self._rm_br_container(self.docker_container)

class BaseRuntimeSmokeTest(Test):

    def _check_cmd_result(self, cmd, return_code, cmd_output, expect_pass=True):
        """
        Check based on return code if command passed or failed as expected
        """
        if return_code == 0 and expect_pass:
            self.log.info("command '%s' succeeded with output:\n%s" %
                          (cmd, cmd_output))
            return True
        elif return_code != 0 and not expect_pass:
            self.log.info("command '%s' failed as expected with output:\n%s" %
                          (cmd, cmd_output))
            return True
        self.error("command '%s' returned unexpected exit status %d; output:\n%s" %
                       (cmd, return_code, cmd_output))
        return False

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

        run_cmd = BaseRuntimeRunCmd()
        for test in smoke_pass:
            try:
                test_ret, test_output = run_cmd.run_docker_cmd(test, rm_container=False)
            except AssertionError as err:
                self.error(err.message)
            except:
                self.error("An unexpected error occurred")
            self._check_cmd_result(test, test_ret, test_output)

        #relying on __del__ from BaseRuntimeRunCmd to remove container
        for test in smoke_fail:
            try:
                test_ret, test_output = run_cmd.run_docker_cmd(test, rm_container=False)
            except AssertionError as err:
                self.error(err.message)
            except:
                self.error("An unexpected error occurred")
            self._check_cmd_result(test, test_ret, test_output, expect_pass=False)


    def testUserManipulation(self):
        """
        Check if can add, remove and modify user
        """

        run_cmd = BaseRuntimeRunCmd()
        #We want to run multiple commands using same docker container
        new_user = "usertest"
        pass_cmds = []
        #Create new user
        pass_cmds.append("adduser %s" % new_user)
        #Make sure user is created
        pass_cmds.append("cat /etc/passwd | grep %s" % new_user)
        pass_cmds.append("ls /home/%s" % new_user)
        #set user password
        pass_cmds.append("usermod --password testpassword %s" % new_user)
        #Test new user functionality
        pass_cmds.append("su - %s -c 'touch ~/testfile.txt'" % new_user)
        #Make sure the file was created by the correct user
        pass_cmds.append("ls -allh /home/%s/testfile.txt | grep '%s %s'" %
                         (new_user, new_user, new_user))
        #Remove user
        pass_cmds.append("userdel -r %s" % new_user)
        for cmd in pass_cmds:
            try:
                test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
            except AssertionError as err:
                self.error(err.message)
            except:
                self.error("An unexpected error occurred")
            self._check_cmd_result(cmd, test_ret, test_output)

        fail_cmds = []
        #Make sure user is removed
        fail_cmds.append("ls /home/%s" % new_user)
        fail_cmds.append("cat /etc/passwd | grep usertest")
        #relying on __del__ from BaseRuntimeRunCmd to remove container
        for cmd in fail_cmds:
            try:
                test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
            except AssertionError as err:
                self.error(err.message)
            except:
                self.error("An unexpected error occurred")
            self._check_cmd_result(cmd, test_ret, test_output, expect_pass=False)


if __name__ == "__main__":
    main()
