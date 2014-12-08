#!/bin/bash

# This script is used as a wrapper for GCC. It's purpose is to provide working
# cross-gcc for use inside Open Build Service.

# Import variables from script, which is generated during the build of
# qemu-accel-* package (from spec-file):
source wrapper-config.sh

# Get the name of executed file (it can be gcc, cc, g++, c++, ...):
COMPILER_NAME=`basename $0`

NATIVE_COMPILER_NAME="/usr/bin/${COMPILER_NAME}"

#TODO: This part of script is legacy. Actually, it disables all cross-utilities,
# including cross toolchain, if variable LIBRARY_PATH is set, and runs native
# compiler. Do we really need to keep this? It came from OpenSUSE.
if [ "$LIBRARY_PATH" ]; then
  mv ${CROSS_ACCELERATION_DIRECTORY}{,.bkp}
  exec ${QEMU_NAME} ${NATIVE_COMPILER_NAME} "$@"
fi

NATIVE_COMPILER_NAME="/usr/bin/${COMPILER_NAME}"
CROSS_COMPILER_NAME="${CROSS_ACCELERATION_DIRECTORY}/usr/bin/${COMPILER_NAME}.real"
CROSS_COMPILER_OPTIONS="$@ -B${CROSS_ACCELERATION_DIRECTORY}/${CROSS_BIN_PREFIX}/bin -B${CROSS_ACCELERATION_DIRECTORY}/${GCC_LIBEXEC_DIRECTORY}"

# Run cross compiler, but set the name of process as native compiler:
exec -a ${NATIVE_COMPILER_NAME} ${CROSS_COMPILER_NAME} ${CROSS_COMPILER_OPTIONS}
