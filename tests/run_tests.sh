#!/bin/bash

for test in /home/tests/unit_tests/*/
do
    echo ========================================================================
    echo  CURRENT TEST: $test
    echo

    python /home/mysh.py < $test/*.in > $test/actual.txt 2> $test/errors.txt
    diffout=`diff $test/*.out $test/actual.txt`
    differr=`diff $test/*.expected $test/errors.txt`

    if [ "$diffout" ] || [ "$differr" ]; then
        echo Test Failed!
        echo
        echo Stdout:
        diff $test/*.out $test/actual.txt
        echo 
        echo Stderr:
        diff $test/*.expected $test/errors.txt
    else
        echo Test Passed!
    fi
    echo
done

for test in /home/tests/end_to_end_tests/*/
do
    echo ========================================================================
    echo  CURRENT TEST: $test
    echo

    python /home/mysh.py < $test/*.in > $test/actual.txt 2> $test/errors.txt
    diffout=`diff $test/*.out $test/actual.txt`
    differr=`diff $test/*.expected $test/errors.txt`

    if [ "$diffout" ] || [ "$differr" ]; then
        echo Test Failed!
        echo
        echo Stdout:
        diff $test/*.out $test/actual.txt
        echo 
        echo Stderr:
        diff $test/*.expected $test/errors.txt
    else
        echo Test Passed!
    fi
    echo
done
