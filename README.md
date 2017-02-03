# baseruntime-docker-tests
CI Tests for the Base Runtime docker image

How to run a test using the avocado framework:

$ avocado run $TEST.py --mux-inject 'run:$TESTPARAM:$VALUE'

e.g.

$ avocado run ./smoke.py --mux-inject 'run:mockcfg:resources/base-runtime-mock.cfg'
