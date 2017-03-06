#!/usr/bin/env python

import os
import subprocess
import re

from avocado import main
from avocado import Test

class BaseRuntimeRunCmd(object):
    docker_container = None

    def _run_cmd(self, cmd):
        try:
            test_output = subprocess.check_output(cmd, stderr = subprocess.STDOUT, shell = True)
        except subprocess.CalledProcessError as e:
            return e.returncode, e.output
        return 0, test_output


    def run_docker_cmd(self, cmd, rm_container=True):
        """
        Execute a docker command. By default it will create a new container
        Once the command finishes the contaier is removed
        """
        cmdline = 'docker run --rm base-runtime-smoke bash -c "%s"' % cmd
        if self.docker_container or not rm_container:
            #Want to execute command and leave contanier running
            if not self.docker_container:
                self.docker_container = self._run_br_contanier_background()
                if not self.docker_container:
                    return 1, "FAIL: run_docker_cmd() - Could not start container"
            cmdline = 'docker exec %s bash -c "%s"' % (self.docker_container, cmd)

        test_ret, test_output = self._run_cmd(cmdline)
        if test_ret !=0:
            #if self.docker_container:
                #Command failed, remove container - Not sure if this is ideal
                #self._rm_br_container(self.docker_container)
                #self.docker_container = None
            return test_ret, test_output

        if self.docker_container and rm_container:
            self._rm_br_container(self.docker_container)
            self.docker_container = None
        return 0, test_output

    def _run_br_contanier_background(self):
        """
        Start new container and keep it running on background
        Return the new container ID
        """
        #Hack to leave container running: http://stackoverflow.com/questions/30209776/docker-container-will-automatically-stop-after-docker-run-d
        cmdline = "docker run -d base-runtime-smoke bash -c 'tail -f /dev/null'"
        test_ret, test_output = self._run_cmd(cmdline)
        if test_ret !=0:
            return test_ret, test_output
        test_output = test_output.strip()
        if not test_output:
            return None
        container_ids = test_output.split('\n')
        if len(container_ids) > 1:
            print "FAIL: _run_br_contanier_background() - Found more containers ID then expected"
            return None
        return container_ids[0]

    def _rm_br_container(self, container_id):
        """
        """
        cmdline = "docker stop %s" % container_id
        test_ret, test_output = self._run_cmd(cmdline)
        if test_ret !=0:
            return e.returncode
        cmdline = "docker rm %s" % container_id
        test_ret, test_output = self._run_cmd(cmdline)
        if test_ret !=0:
            return test_ret
        return 0

    #Probably not the best way, but I could not find away to guarantee container will be removed
    def __del__(self):
        if self.docker_container:
            self._rm_br_container(self.docker_container)

class BaseRuntimeSmokeTest(Test):

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
        cnt = 0
        for test in smoke_pass:
            cnt += 1
            rm_container = False
            if cnt == len(smoke_pass):
                rm_container = True
            test_ret, test_output = run_cmd.run_docker_cmd(test, rm_container=rm_container)
            if test_ret == 0:
                self.log.info("smoke test command '%s' succeeded with output:\n%s" %
                    (test, test_output))
            else:
                self.error("command '%s' returned unexpected exit status %d; output:\n%s" %
                    (test, test_ret, test_output))


        for test in smoke_fail:
            test_ret, test_output = run_cmd.run_docker_cmd(test)
            if test_ret == 0:
                self.error("smoke test command '%s' succeeded unexpectly with output:\n%s" %
                    (test, test_output))
            else:
                self.log.info("command '%s' returned exit status %d; output:\n%s" %
                    (test, test_ret, test_output))


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
        self.log.error("command '%s' returned unexpected exit status %d; output:\n%s" %
                       (cmd, return_code, cmd_output))
        return False



    def testUserManipulation(self):
        """
        Check if can add, remove and modify user
        """

        error = False

        run_cmd = BaseRuntimeRunCmd()
        #We want to run multiple commands using same docker container
        #Create new user
        cmd = "adduser usertest"
        test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
        if not self._check_cmd_result(cmd, test_ret, test_output):
            error = True

        #Make sure user is created
        cmd = "cat /etc/passwd | grep usertest"
        test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
        if not self._check_cmd_result(cmd, test_ret, test_output):
            error = True

        cmd = "ls /home/usertest"
        test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
        if not self._check_cmd_result(cmd, test_ret, test_output):
            error = True

        #set user password
        cmd = "usermod --password testpassword usertest"
        test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
        if not self._check_cmd_result(cmd, test_ret, test_output):
            error = True

        #cmd = "echo test | passwd usertest --stdin"
        #test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
        #if not self._check_cmd_result(cmd, test_ret, test_output):
        #    error = True

        #Test new user functionality
        cmd = "su - usertest; touch ~/testfile.txt"
        test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
        if not self._check_cmd_result(cmd, test_ret, test_output):
            error = True

        cmd = "su - usertest; ls -allh ~/testfile.txt"
        test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
        if not self._check_cmd_result(cmd, test_ret, test_output):
            error = True


        #Remove user
        cmd = "userdel -r usertest"
        test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
        if not self._check_cmd_result(cmd, test_ret, test_output):
            error = True

        #Make sure user is removed
        cmd = "ls /home/usertest"
        test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=False)
        if not self._check_cmd_result(cmd, test_ret, test_output, expect_pass=False):
            error = True

        cmd = "cat /etc/passwd | grep usertest"
        #container can be removed now
        test_ret, test_output = run_cmd.run_docker_cmd(cmd, rm_container=True)
        if not self._check_cmd_result(cmd, test_ret, test_output, expect_pass=False):
            error = True

        if error:
            self.error("UserManipulation test failed")


if __name__ == "__main__":
    main()
