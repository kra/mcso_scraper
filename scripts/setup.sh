#!/bin/bash
DIR=`dirname $0`
cd $DIR/.. && source env/bin/activate && env PYTHONPATH=. setup/setup.py $*
