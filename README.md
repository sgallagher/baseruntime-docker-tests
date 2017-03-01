# baseruntime-docker-tests
CI Tests for the Base Runtime docker image

How to run a test using the [avocado testing framework](http://avocado-framework.github.io/):

    $ avocado run $TEST.py --mux-inject 'run:$TESTPARAM:$VALUE'

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

The test scripts need to be passed the base-runtime mock configuration file, provided on the command line via the [avocado's parameter passing mechanism](http://avocado-framework.readthedocs.io/en/latest/WritingTests.html#accessing-test-parameters).

Run each of the phases in sequence. e.g.,

    $ avocado run ./setup.py --mux-inject 'run:mockcfg:resources/base-runtime-mock.cfg'
    $ avocado run ./smoke.py
    $ avocado run ./teardown.py --mux-inject 'run:mockcfg:resources/base-runtime-mock.cfg'

In the future, additional test scripts can be run between the setup and teardown.
