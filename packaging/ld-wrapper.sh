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

CROSS_LD_ARGUMENTS=$@
# Add option "--sysroot=/" if there is no option "--sysroot" in command line.
if [[ ${CROSS_LD_ARGUMENTS} != "*--sysroot=*" ]] ; then
  CROSS_LD_ARGUMENTS="${CROSS_LD_ARGUMENTS} --sysroot=/"
fi

NATIVE_LD_ARGUMENTS=$@
# Remove prefix /emul/*-for* from command-line arguments:
NATIVE_LD_ARGUMENTS=`echo ${NATIVE_LD_ARGUMENTS} | sed -e "s#${CROSS_ACCELERATION_DIRECTORY}##g"`

# Remove option "--sysroot=*" from command-line arguments:
NATIVE_LD_ARGUMENTS=`echo ${NATIVE_LD_ARGUMENTS} | sed -e "s#--sysroot=[^[:space:]]\+# #g"`

# Add option -L so that to advise ld where to look for GCC binaries.
NATIVE_LD_ARGUMENTS="${NATIVE_LD_ARGUMENTS} -L${GCC_LIBEXEC_DIRECTORY}"

# Get the name of executed file (it can be ld, ld.bfd, ld.gold):
LD_NAME=`basename $0`

# Set the namd of cross ld:
CROSS_LD_NAME="${CROSS_ACCELERATION_DIRECTORY}/${CROSS_BIN_PREFIX}/${LD_NAME}.real"

# Set the name of native ld:
NATIVE_LD_NAME="${NATIVE_BIN_PREFIX}/${LD_NAME}"

# Run cross ld, and if it fails, then run native ld with (almost) the same
# command-line arguments:
${CROSS_LD_NAME} ${CROSS_LD_ARGUMENTS} \
	|| ${QEMU_NAME} ${NATIVE_LD_NAME} ${NATIVE_LD_ARGUMENTS}
