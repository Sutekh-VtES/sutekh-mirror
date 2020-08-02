#!/bin/bash

# Set the right database url

if [ "$TESTDB" = "mysql" ]; then
     export SUTEKH_TEST_DB="mysql://root:@localhost/sutekh_test?driver=connector"
     echo "Running on $SUTEKH_TEST_DB"
elif [ "$TESTDB" = "postgres" ]; then
     export SUTEKH_TEST_DB="postgres://postgres:@localhost/sutekh_test?driver=psycopg&charset=utf-8"
     echo "Running on $SUTEKH_TEST_DB"
else
   echo "Running tests on sqlite memory DB"
fi

cd sutekh
pytest
