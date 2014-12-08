#!/bin/bash

# This script is used as a wrapper for Dynamic Linker (ld) from binutils
# package. It's purpose is to provide working cross-ld for use inside Open
# Build Service.

# Import variables from script, which is generated during the build of
# qemu-accel-* package (from spec-file):
source wrapper-config.sh

# If the variable LD_LIBRARY_PATH is set, options are parsed so that to
# remove option "--sysroot" from command line arguments.
# TODO: This part of script is legacy (inherited from old OpenSUSE version of
# qemu-accel), so maybe it is not needed in our environemt.
if [ -n "$LD_LIBRARY_PATH" ]; then
  # arguments as file
  if [ "${1:0:1}" = "@" ]; then
    FILE="${1:1}"
    grep -v -- "--sysroot=" "$FILE" > "$FILE.fixed"
    mv "$FILE.fixed" "$FILE"
  fi

  # cross ld does not work correctly using LD_LIBRARY_PATH, use arm version
  args=()
  for i in "$@"; do
    if [ "${i:0:10}" != "--sysroot=" ]; then
      args=(${args[@]} "$i")
    fi
  done
  exec ${QEMU_NAME} /usr/bin/ld `echo "${args[@]}" | sed -e "s#${CROSS_ACCELERATION_DIRECTORY}##g"`
fi

# Get the name of executed file (it can be ld, ld.bfd, ld.gold):
LD_NAME=`basename $0`

# Set the namd of cross ld:
CROSS_LD_NAME="${CROSS_ACCELERATION_DIRECTORY}/${CROSS_BIN_PREFIX}/${LD_NAME}.real"

# Set the name of native ld:
NATIVE_LD_NAME="${NATIVE_BIN_PREFIX}/${LD_NAME}"

for i in "$@"; do
  if [ "${i:0:10}" = "--sysroot=" ]; then
    ${CROSS_LD_NAME} "$@" || ${QEMU_NAME} ${NATIVE_LD_NAME} -L${GCC_LIBEXEC_DIRECTORY} `echo "$@" | sed -e "s#${CROSS_ACCELERATION_DIRECTORY}##g;s#--sysroot=[^[:space:]]\+# #g"`
    exit $?
  fi
done

${CROSS_LD_NAME} --sysroot=/ "$@" || ${QEMU_NAME} ${NATIVE_LD_NAME} -L${GCC_LIBEXEC_DIRECTORY} `echo "$@" | sed -e "s#${CROSS_ACCELERATION_DIRECTORY}##g;s#--sysroot=[^[:space:]]\+# #g"`
