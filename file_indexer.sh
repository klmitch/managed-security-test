#!/bin/sh

# Select the top-level directory and the virtual environment directory
top_dir=`dirname $0`
venv_dir=$top_dir/.venv

# Set up the virtual environment
if [ ! -d $venv_dir ]; then
    # Ensure virtualenv is installed
    if which virtualenv >/dev/null 2>&1; then
	:
    else
	echo 'Please install the Python package "virtualenv".' >&2
	exit 1
    fi

    virtualenv -q $venv_dir

    # Make sure the virtual environment was created
    if [ ! -d $venv_dir ]; then
	echo 'Failed to create the virtual environment.' >&2
	exit 127
    fi

    # Install the solution into the virtual environment
    $venv_dir/bin/pip -q install -r $top_dir/requirements.txt
    $venv_dir/bin/pip -q install -e $top_dir
fi

# Invoke the solution
$venv_dir/bin/file_indexer "$@"
