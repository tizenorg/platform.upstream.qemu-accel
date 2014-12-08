#!/bin/bash

cp qemu-accel.spec.in qemu-accel-armv7l.spec
sed -i qemu-accel-armv7l.spec \
	-e "s/EMULATED_ARCH_LONG/armv7l/g" \
	-e "s/EMULATED_ARCH_SHORT/arm/g" \
	-e "s/EMULATED_ARCH_SYNONIM/arm/g" \
	-e "s/EMULATED_ARCH_TRIPLE_SHORT/\%\{emulated_arch_short\}-tizen-linux-gnueabi/g" \
	-e "s/EMULATED_ARCH_TRIPLE_LONG/\%\{emulated_arch_long\}-tizen-linux-gnueabi/g"

cp qemu-accel.spec.in qemu-accel-aarch64.spec
sed -i qemu-accel-aarch64.spec \
	-e "s/EMULATED_ARCH_LONG/aarch64/g" \
	-e "s/EMULATED_ARCH_SHORT/aarch64/g" \
	-e "s/EMULATED_ARCH_SYNONIM/arm64/g" \
	-e "s/EMULATED_ARCH_TRIPLE_SHORT/\%\{emulated_arch_short\}-tizen-linux/g" \
	-e "s/EMULATED_ARCH_TRIPLE_LONG/\%\{emulated_arch_long\}-tizen-linux/g"

