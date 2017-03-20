"""
cleanup docker container/images and mock root for smoke testing
"""

import logging
import subprocess
import re


log = logging.getLogger('avocado.test')

def cleanup_docker_and_mock(mockcfg, img_name):

    # Clean-up old test artifacts (docker containers, image, mock root)

    docker_containerlist_cmdline = 'docker ps --filter=ancestor=%s -a -q' % img_name
    try:
        containerlist = subprocess.check_output(docker_containerlist_cmdline,
            stderr = subprocess.STDOUT, shell = True)
    except subprocess.CalledProcessError as e:
        log.error("command '%s' returned exit status %d; output:\n%s" %
            (e.cmd, e.returncode, e.output))
        raise
    else:
        log.info("docker container list with '%s' succeeded with output:\n%s" %
            (docker_containerlist_cmdline, containerlist))

    if containerlist:
        containers = re.sub('[\r\n]+', ' ', containerlist)
        log.info("docker containers using image %s need to be removed: %s\n" %
            (img_name, containers));
        docker_teardown_cmdline = 'docker rm -f %s' % containers
        try:
            docker_teardown_output = subprocess.check_output(docker_teardown_cmdline,
                stderr = subprocess.STDOUT, shell = True)
        except subprocess.CalledProcessError as e:
            log.error("command '%s' returned exit status %d; output:\n%s" %
                (e.cmd, e.returncode, e.output))
            raise
        else:
            log.info("docker container teardown with '%s' succeeded with output:\n%s" %
                (docker_teardown_cmdline, docker_teardown_output))
    else:
        log.info("no docker containers are using image %s\n" % img_name)

    docker_teardown_cmdline = 'docker rmi %s' % img_name
    try:
        docker_teardown_output = subprocess.check_output(docker_teardown_cmdline,
            stderr = subprocess.STDOUT, shell = True)
    except subprocess.CalledProcessError as e:
        if "No such image" not in e.output:
            log.error("command '%s' returned exit status %d; output:\n%s" %
                (e.cmd, e.returncode, e.output))
            raise
        else:
            log.info("No existing docker image named %s" % img_name)
    else:
        log.info("docker teardown with '%s' succeeded with output:\n%s" %
            (docker_teardown_cmdline, docker_teardown_output))

    mock_teardown_cmdline = ['mock', '-r', mockcfg, '--scrub=all']
    try:
        mock_teardown_output = subprocess.check_output(mock_teardown_cmdline,
            stderr = subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        log.error("command '%s' returned exit status %d; output:\n%s" %
            (e.cmd, e.returncode, e.output))
        raise
    log.info("mock teardown with '%s' succeeded with output:\n%s" %
        (mock_teardown_cmdline, mock_teardown_output))





