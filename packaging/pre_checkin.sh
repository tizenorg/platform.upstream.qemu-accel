#!/bin/bash

# the script takes qemu-accel.spec and creates the qemu-accel-* packages
for arch in armv7l aarch64; do

   echo -n "Building package for $arch --> gcc-$arch ..."

   echo "%define cross $arch" > qemu-accel-${arch}.spec
   echo "%define $arch 1" >> qemu-accel-${arch}.spec
   echo "" >> qemu-accel-${arch}.spec
   cat qemu-accel.spec >> qemu-accel-${arch}.spec
   echo " done."
done

