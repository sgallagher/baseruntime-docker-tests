# baseruntime-docker-tests
CI Tests for the Base Runtime docker image

How to run a test using the [avocado testing framework](http://avocado-framework.github.io/):

    $ avocado run $TEST.py [ --mux-inject 'run:$TESTPARAM:$VALUE' ... ]

## Setup

Install prerequisite RPMs if necessary:

* python2-aexpect - dependency for python-avocado
* python2-avocado - avocado testing framework
* python2-modulemd - Module metadata manipulation library
* docker - Automates deployment of containerized applications

## Docker setup

Configure docker to run as your (non-root!) userid:

https://docs.docker.com/engine/installation/linux/linux-postinstall/#manage-docker-as-a-non-root-user

Configure docker to start automatically (and start it):

https://docs.docker.com/engine/installation/linux/linux-postinstall/#manage-docker-as-a-non-root-user#configure-docker-to-start-on-boot

## Background

Avocado starts a fresh process per test method and runs setup/teardown methods
each time. We can't afford to have that cause our docker image be repeatedly
created/removed. Thus, these CI tests have been split up into three phases:
* setup: creates the docker image
* smoke: runs the tests
* teardown: removes the docker image

## Running these tests

Run each of the phases in sequence. e.g.,

    $ avocado run ./setup.py
    $ avocado run ./smoke.py
    $ avocado run ./teardown.py

In the future, additional test scripts can be run between the setup and teardown.

## Test script configuration overrides

Optional test script configuration overrides can provided on the command line using [avocado's parameter passing mechanism](http://avocado-framework.readthedocs.io/en/latest/WritingTests.html#accessing-test-parameters) in the following manner:

    $ avocado run $TEST.py [ --mux-inject 'run:$TESTPARAM:$VALUE' ... ]

### mockcfg - path to mock configuration file

The setup.py and teardown.py scripts need to read a base-runtime mock configuration file. The default path is 'resources/base-runtime-mock.cfg' relative to the directory where the test script resides. This path can be overridden with the 'mockcfg' parameter.

### compiler-test-dir - path to compiler test resource directory

The smoke.py script needs to access a base-runtime compiler test resource directory. The default path is 'resources/hello-world' relative to the directory where the test script resides. This path can be overridden with the 'compiler-test-dir' parameter.

### docker-image-name - path to mock configuration file

All of the scripts need to know the name to use for the base-runtime docker image. The default name is 'base-runtime-smoke'. This name can be overridden with the 'docker-image-name' parameter.
