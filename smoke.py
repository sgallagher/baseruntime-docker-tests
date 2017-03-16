#!/usr/bin/env python

import os
import subprocess
import re
import shutil
import stat
import tarfile
import tempfile

from avocado import main
from avocado import Test

import brtconfig


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


    def run_docker_cmd(self, cmd, img_name, rm_container=True):
        """
        Execute a docker command. By default it will create a new container
        Once the command finishes the container is removed
        """
        cmdline = 'docker run --rm %s bash -c "%s"' % (img_name, cmd)

        if self.docker_container or not rm_container:
            #Want to execute command and leave container running
            if not self.docker_container:
                self.docker_container = self._run_br_container_background(img_name)
            cmdline = 'docker exec %s bash -c "%s"' % (self.docker_container, cmd)

        test_ret, test_output = self._run_cmd(cmdline)

        if self.docker_container and rm_container:
            self._rm_br_container(self.docker_container)
            self.docker_container = None

        return test_ret, test_output

    def _run_br_container_background(self, img_name):
        """
        Start new container and keep it running on background
        Return the new container ID
        """
        #Hack to leave container running: http://stackoverflow.com/questions/30209776/docker-container-will-automatically-stop-after-docker-run-d
        cmdline = "docker run -d %s bash -c 'tail -f /dev/null'" % img_name
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

    def setUp(self):

        self.compiler_resource_dir = brtconfig.get_compiler_test_dir(self)
        self.br_image_name = brtconfig.get_docker_image_name(self)
        self.compiler_test_dir = None

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
                test_ret, test_output = run_cmd.run_docker_cmd(
                    test, self.br_image_name, rm_container=False)
            except AssertionError as err:
                self.error(err.message)
            except:
                self.error("An unexpected error occurred")
            self._check_cmd_result(test, test_ret, test_output)

        #relying on __del__ from BaseRuntimeRunCmd to remove container
        for test in smoke_fail:
            try:
                test_ret, test_output = run_cmd.run_docker_cmd(
                    test, self.br_image_name, rm_container=False)
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
                test_ret, test_output = run_cmd.run_docker_cmd(
                    cmd, self.br_image_name, rm_container=False)
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
                test_ret, test_output = run_cmd.run_docker_cmd(
                    cmd, self.br_image_name, rm_container=False)
            except AssertionError as err:
                self.error(err.message)
            except:
                self.error("An unexpected error occurred")
            self._check_cmd_result(cmd, test_ret, test_output, expect_pass=False)


    def _prepare_compiler_test_directory(self):

        # create a temporary directory
        tmpdir = tempfile.mkdtemp()

        self.log.info("Compiler test temporary directory is %s" % tmpdir)

        # Copy the `hello.sh` script from this resource directory into the
        # temporary directory
        src = os.path.join(self.compiler_resource_dir, "hello.sh")
        dest = os.path.join(tmpdir, "hello.sh")
        try:
            shutil.copy(src, dest)
        except shutil.Error as e:
            self.log.info('Error: %s' % e)
        except IOError as e:
            self.log.info('Error: %s' % e.strerror)

        # make sure destination script is executable
        st = os.stat(dest)
        os.chmod(dest, st.st_mode | stat.S_IEXEC)

        # Place a gzipped tarball of `hello.c` and `Makefile` from the
        # resource directory into the temporary directory with the name
        # `hello.tgz`.
        dest = os.path.join(tmpdir, "hello.tgz")
        tar = tarfile.open(dest, "w:gz")
        for f in ["hello.c", "Makefile"]:
            src = os.path.join(self.compiler_resource_dir, f)
            tar.add(src, arcname=f)
        tar.close()

        self.compiler_test_dir = tmpdir

    def _cleanup_compiler_test_directory(self):

        # clean up the temporary directory
        if self.compiler_test_dir:
            self.log.info("cleaning up compiler test directory")
            shutil.rmtree(self.compiler_test_dir, ignore_errors=True)

    def testCompiler(self):
        """
        Run a basic C compiler test on our docker image.

        This actually tests the integration of several things, including the
        ability to install packages, extract a gzipped tarball, run make to
        compile a very simple C program, and run the compiled executable.
        """

        self._prepare_compiler_test_directory()

        # mount the prepared compiler test directory in the docker container
        # as /mnt, then run the "hello.sh" test script within
        cmdline = 'docker run -v "%s:/mnt:z" --rm %s bash -c "/mnt/hello.sh"' % (
            self.compiler_test_dir, self.br_image_name)
        try:
            process = subprocess.Popen(cmdline, shell=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            self.error("An unexpected error occurred while running '%s'" % cmdline)
        test_stdout, test_stderr = process.communicate()

        if process.returncode:
            self.error("command '%s' returned exit status %d; output:\n%s\nstderr:\n%s" %
                       (cmdline, process.returncode, test_stdout, test_stderr))

        self.log.info("command '%s' succeeded with output:\n%s\nstderr:\n%s" %
                      (cmdline, test_stdout, test_stderr))

        # make sure we get exactly what we expect on stdout
        # (all other output from commands in the script were sent to stderr)
        expected_stdout = 'Hello, world!\n'
        self.log.info("checking that compiler test returned expected output: %s" %
                      repr(expected_stdout))
        if test_stdout != expected_stdout:
            self.error("compiler test did not return unexpected output: %s" %
                       repr(test_stdout))

    def tearDown(self):
        """
        Tear-down
        """

        self._cleanup_compiler_test_directory()

if __name__ == "__main__":
    main()
