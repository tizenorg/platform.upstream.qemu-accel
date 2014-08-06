#
# spec file for package qemu-accel-armv7l
#
# Copyright (c) 2012 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


# Choose which gcc hijack method (if any) to use.
# Only select one of the two at a time!
%define hijack_gcc 1

# Check whether macro "gcc_version" was defined via project config
%if 0%{?gcc_version}
%else
# If the macro was undefined, set it to this default value:
%define gcc_version 49
%endif
%{expand:%%define gcc_version_dot %(echo "%{gcc_version}" | sed -e "s/\([0-9]\)\([0-9]\)/\1.\2/g")}
Name:           qemu-accel-armv7l
Version:        0.4
Release:        0
VCS:            platform/upstream/qemu-accel#submit/tizen/20131025.201555-0-g039eeafa6b52fd126f38fed9cd2fdf36a26a3065
AutoReqProv:    off
BuildRequires:  cross-arm-binutils
BuildRequires:  cross-armv7l-gcc%{gcc_version}-icecream-backend
#BuildRequires:  expect
BuildRequires:  fdupes
BuildRequires:  glibc-locale
BuildRequires:  gcc-c++
BuildRequires:  gettext-runtime
BuildRequires:  gettext-tools
BuildRequires:  m4
# required for xxd
BuildRequires:  vim
BuildRequires:  patchelf
#BuildRequires:  rpmlint-mini
BuildRequires:  qemu-linux-user
Requires:       coreutils
Summary:        Native binaries for speeding up cross compile
License:        GPL-2.0
Group:          Development/Libraries/Cross
ExclusiveArch:  x86_64 %ix86

# default path in qemu
%define HOST_ARCH %(echo %{_host_cpu} | sed -e "s/i.86/i586/;s/ppc/powerpc/;s/sparc64.*/sparc64/;s/sparcv.*/sparc/;")
%define our_path /emul/%{HOST_ARCH}-for-arm
%ifarch %ix86
%define icecream_cross_env cross-armv7l-gcc%{gcc_version}-icecream-backend_i386
%else
%define icecream_cross_env cross-armv7l-gcc%{gcc_version}-icecream-backend_x86_64
%endif

%description
This package is used in armv7l architecture builds using qemu to speed up builds
with native binaries.
 This should not be installed on systems, it is just intended for qemu environments.

%prep
%setup -q -D -T -n .

%build

%install
binaries="/%_lib/libnsl.so.1 /%_lib/libnss_compat.so.2 %{_libdir}/rpm-plugins/msm.so" # loaded via dlopen by glibc
%ifarch %ix86
  LD="/lib/ld-linux.so.2"
%else
%ifarch x86_64
  LD="/lib64/ld-linux-x86-64.so.2"
%else
  echo "ERROR unhandled arch"
  exit 1
%endif
%endif

# XXX this fails with the following error:
#     /opt/testing/bin/python: error while loading shared libraries: libpython2.7.so.1.0: wrong ELF class: ELFCLASS32

for executable in $LD \
   /usr/bin/{bash,rpm,rpmdb} \
   /usr/bin/{gzip,grep,egrep,sed,tar} \
%ifarch %ix86
   /usr/lib/libnssdbm3.so /usr/lib/libsoftokn3.so /lib/libfreebl3.so \
%else
   /usr/lib64/libnssdbm3.so /usr/lib64/libsoftokn3.so /lib64/libfreebl3.so \
%endif
   /usr/bin/{bzip2,cat,expr,make,m4,mkdir,msgexec,msgfmt,msgcat,msgmerge,mv,patch,rm,rmdir,rpmbuild,xz,xzdec} \
   /usr/arm-tizen-linux-gnueabi/bin/{as,ar,ld,ld.bfd,objcopy,objdump}
do  
  binaries="$binaries $executable `ldd $executable | sed -n 's,.*=> \(/[^ ]*\) .*,\1,p'`"
done

%if %hijack_gcc
# extract cross-compiler
mkdir -p cross-compiler-tmp
for executable in $(tar -C cross-compiler-tmp -xvzf /usr/share/icecream-envs/cross-armv7l-gcc%{gcc_version}-icecream-backend_*.tar.gz); do
    if [ ! -d "cross-compiler-tmp/$executable" ]; then
        binaries="$binaries cross-compiler-tmp/$executable"
    fi
done
%endif


%if %hijack_gcc
# Install 
mkdir -p %buildroot%{our_path}/usr/share/icecream-envs/%{icecream_cross_env}
cp -a /usr/share/icecream-envs/%{icecream_cross_env}.tar.gz \
      %buildroot%{our_path}/usr/share/icecream-envs
# And extract it for direct usage
tar xvz -C %buildroot%{our_path}/usr/share/icecream-envs/%{icecream_cross_env} -f /usr/share/icecream-envs/cross-armv7l-gcc%{gcc_version}-icecream-backend_*.tar.gz
# It needs a tmp working directory which is writable
install -d -m0755 %buildroot%{our_path}/usr/share/icecream-envs
%endif

for binary in $binaries
do
  outfile=%buildroot%{our_path}$(echo $binary | sed 's:cross-compiler-tmp::;s:/opt/cross/armv7l-tizen-linux-gnueabi:/usr:')
  [ -f $outfile ] && continue
  mkdir -p ${outfile%/*}
  cp -aL $binary $outfile
  # XXX hack alert! Only works for armv7l-on-x86_64
%ifarch x86_64
  [ "$(basename $outfile)" = "bash" ] && sed -i 's/x86_64/armv7l/g' "$outfile"
%endif
  objdump -s -j .rodata -j .data $outfile | sed 's/^ *\([a-z0-9]*\)/\1:/' | \
      grep ': ' | grep -v 'file format' | grep -v 'Contents of section' | \
      xxd -g4 -r - $outfile.data
  if grep -q "%{HOST_ARCH}"$outfile.data; then
    echo "ERROR file $binary leaks host information into the guest"
    exit 1
  fi
  rm -f $outfile.data
  [ "$binary" == "$LD" ] && continue
  patchelf --debug --set-rpath "%our_path/%_lib:%our_path%_libdir" $outfile
# not all binaries have an .interp section
  if patchelf --print-interpreter $outfile; then
    patchelf --debug --set-interpreter %{our_path}$LD $outfile
  fi
done

# make gconv libraries available (needed for msg*)
%ifarch x86_64
mkdir -p %{buildroot}/usr/lib64/gconv
cp -a /usr/lib64/gconv/* "%{buildroot}/usr/lib64/gconv/"
%endif

# create symlinks for bash
#ln -sf ../usr/bin/bash "%{buildroot}%{our_path}/bin/sh"
#ln -sf ../../bin/bash "%{buildroot}%{our_path}/usr/bin/sh"

# binutils needs to be exposed in /usr/bin
for i in ar ld ld.bfd objcopy objdump; do
  ln -s ../arm-tizen-linux-gnueabi/bin/$i %{buildroot}%{our_path}/usr/bin/$i
done
pushd %{buildroot}%{our_path} &&  ln -s usr/bin && popd

%if %hijack_gcc
# create symlinks for lib64 / lib mappings (gcc!)
mkdir -p "%{buildroot}%{our_path}/usr/lib/"
# binutils secondary directories
mkdir -p %{buildroot}%{our_path}/usr/armv7l-tizen-linux-gnueabi/
ln -sf ../bin %{buildroot}%{our_path}/usr/armv7l-tizen-linux-gnueabi/bin

%ifarch %ix86
ln -sf ../lib/gcc "%{buildroot}%{our_path}/usr/lib/gcc"
%else
ln -sf ../lib64/gcc "%{buildroot}%{our_path}/usr/lib/gcc"
%endif
# g++ can also be called c++
ln -sf g++ "%{buildroot}%{our_path}/usr/bin/c++"
# gcc can also be called cc
ln -sf gcc "%{buildroot}%{our_path}/usr/bin/cc"
# gcc can also be called gcc-%{gcc_version_dot}
ln -sf gcc "%{buildroot}%{our_path}/usr/bin/gcc-%{gcc_version_dot}"

# nasty hack: If LIBRARY_PATH is set, native gcc adds the contents to its
#             library search list, but cross gcc does not. So switch to all
#             native in these situations.
for compiler in gcc g++
do
  mv %{buildroot}%{our_path}/usr/bin/${compiler}{,.real}
echo '#!/bin/bash
if [ "$LIBRARY_PATH" ]; then
  mv %{our_path}{,.bkp}
    exec /usr/bin/qemu-arm /usr/bin/'${compiler}' "$@"
fi
  exec -a /usr/bin/'${compiler}' %{our_path}/usr/bin/'${compiler}'.real "$@" -B%{our_path}/usr/armv7l-tizen-linux-gnueabi/bin -B%{our_path}/%{_libdir}/gcc/armv7l-tizen-linux-gnueabi/%{gcc_version_dot}
  ' > %{buildroot}%{our_path}/usr/bin/${compiler}
  chmod +x %{buildroot}%{our_path}/usr/bin/${compiler}
done
#
# as is not writing right EABI ELF header inside of arm environment for unknown reason
#
mv %{buildroot}%{our_path}/usr/bin/as{,.real}
echo '#!/bin/bash
exec -a /usr/bin/as %{our_path}/usr/bin/as.real -meabi=5 "$@"
' > %{buildroot}%{our_path}/usr/bin/as
chmod +x %{buildroot}%{our_path}/usr/bin/as

# allow abuild to do the mv
chmod 755 %{buildroot}/emul

# make cross ld work with emulated compilers
mv %{buildroot}%{our_path}/usr/arm-tizen-linux-gnueabi/bin/ld{,.real}
echo '#!/bin/bash
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
  exec /usr/bin/qemu-arm /usr/bin/ld `echo "${args[@]}" | sed -e "s#%{our_path}##"`
fi
for i in "$@"; do
  if [ "${i:0:10}" = "--sysroot=" ]; then
    exec -a "$0" %{our_path}/usr/arm-tizen-linux-gnueabi/bin/ld.real "$@"
  fi
done

%{our_path}/usr/arm-tizen-linux-gnueabi/bin/ld.real --sysroot=/ "$@" || ( /usr/bin/qemu-arm /usr/armv7l-tizen-linux-gnueabi/bin/ld -L/usr/lib/gcc/armv7l-tizen-linux-gnueabi/4.9/ `echo "$@" | sed -e "s#%{our_path}##"` ; echo "Running native ld, because cross ld has failed with the following error: " )
' > %{buildroot}%{our_path}/usr/arm-tizen-linux-gnueabi/bin/ld
chmod +x %{buildroot}%{our_path}/usr/arm-tizen-linux-gnueabi/bin/ld

# To support gcc sysroot
mkdir -p %{buildroot}/usr/armv7l-tizen-linux-gnueabi
ln -sf .. %{buildroot}/usr/armv7l-tizen-linux-gnueabi/usr
ln -sf ../include %{buildroot}/usr/armv7l-tizen-linux-gnueabi/include
%endif

# Make QEMU available through /qemu
mkdir %buildroot/qemu
cp -L /usr/bin/qemu-arm{,-binfmt} %buildroot/qemu/

%fdupes -s %{buildroot}

export NO_BRP_CHECK_RPATH="true"

# Install glibc-locale, otherwise msgmerge >= 0.18.3 fails
%ifarch x86_64
cp -R /usr/lib64/gconv %{buildroot}%{our_path}/usr/lib64
cp -R /usr/lib/locale %{buildroot}%{our_path}/usr/lib
chmod 755 %{buildroot}%{our_path}/usr/lib/locale
chmod 755 %{buildroot}%{our_path}/usr/lib64/gconv
%else
cp -R /usr/lib/{gconv,locale} %{buildroot}%{our_path}/usr/lib
chmod 755 %{buildroot}%{our_path}/usr/lib/{gconv,locale}
%endif
cp -R /usr/share/locale %{buildroot}%{our_path}/usr/share
# Fix permissions for abuild
chmod 755 %{buildroot}%{our_path}/usr/share/locale

%post
set -x
if [ $(uname -m) = armv7l ]; then
    builtin echo "armv7l arch"
    # XXX find a way around this for cross-gcc
    mkdir -p /usr/lib64/gcc /lib64 || true
    ln -sf ../../lib/gcc/armv7l-tizen-linux-gnueabi /usr/lib64/gcc/armv7l-tizen-linux-gnueabi || true
    ln -sf %{our_path}/lib64/libnsl.so.1 /lib64/libnsl.so.1 || true
fi
# use qemu-arm{,-binfmt} from a  safe directory, so even overwriting
# /usr/bin/$file won't affect our ability to run arm code

# load the binfmt_misc module
if [ ! -d /proc/sys/fs/binfmt_misc ]; then
  builtin echo "Calling modprobe"
  /sbin/modprobe binfmt_misc
fi

did_mount_it=""

if [ ! -f /proc/sys/fs/binfmt_misc/register ]; then
  builtin echo "mounting binfmt_misc"
  mount binfmt_misc -t binfmt_misc /proc/sys/fs/binfmt_misc
  did_mount_it=1
fi

if [ -e /proc/sys/fs/binfmt_misc/arm ]; then
    builtin echo "Registering accelerated handler"
    builtin echo -1 > /proc/sys/fs/binfmt_misc/arm
    builtin echo ':arm:M::\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/qemu/qemu-arm-binfmt:P' > /proc/sys/fs/binfmt_misc/register
fi

if [ $did_mount_it ]; then 
  builtin echo "Unmounting again.";
  umount /proc/sys/fs/binfmt_misc
fi

builtin echo "All done"

# Fix up sysroot paths
rm -rf /usr/armv7l-tizen-linux-gnueabi/lib
ln -s /lib /usr/armv7l-tizen-linux-gnueabi/usr/lib

%files
%defattr(-,root,root)  
%dir /usr/armv7l-tizen-linux-gnueabi
/usr/armv7l-tizen-linux-gnueabi/usr
/usr/armv7l-tizen-linux-gnueabi/include
/emul
/qemu
%ifarch x86_64
/usr/lib64
%endif

%changelog
