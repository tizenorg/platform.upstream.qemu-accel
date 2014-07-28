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

# Set to 1 if you want to use qemu-aarch64-binfmt, not normal qemu
%define use_binfmt_binary 1

# Set to 1 if you want to use cross binary executables
%define use_cross_binaries 1

# Whether to use different cross binaries and their libraries
%define use_cross_ldso 1
%define use_cross_nss 1
%define use_cross_bash 1
%define use_cross_rpm 1
%define use_cross_archivators 1
%define use_cross_stream_editors 1
%define use_cross_coreutils 1
%define use_cross_gettext_tools 1
%define use_cross_make 1
%define use_cross_m4 1
%define use_cross_patch 1
%define use_cross_binutils 1
%define use_cross_su 0

%if 0%{!?use_cross_binaries}
%define hijack_gcc 0
%endif

Name:           qemu-accel-aarch64
Version:        0.4
Release:        0
VCS:            platform/upstream/qemu-accel#ca50f86f943b96de45d50929495024471f0060aa
AutoReqProv:    off
BuildRequires:  cross-aarch64-binutils
%if %hijack_gcc
BuildRequires:  cross-aarch64-gcc49-icecream-backend
%define gcc_version 4.9
%endif
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
BuildRequires:  rpmlint-mini
BuildRequires:  qemu-linux-user
Requires:       coreutils
BuildRequires:  -gcc -gcc49
Summary:        Native binaries for speeding up cross compile
License:        GPL-2.0
Group:          Development/Libraries/Cross
ExclusiveArch:  x86_64 %ix86

# default path in qemu
%define HOST_ARCH %(echo %{_host_cpu} | sed -e "s/i.86/i586/;s/ppc/powerpc/;s/sparc64.*/sparc64/;s/sparcv.*/sparc/;")
%define our_path /emul/%{HOST_ARCH}-for-aarch64
%ifarch %ix86
%define icecream_cross_env cross-aarch64-gcc49-icecream-backend_i386
%else
%define icecream_cross_env cross-aarch64-gcc49-icecream-backend_x86_64
%endif
%define binaries_binutils addr2line ar as elfedit gprof ld ld.bfd nm objcopy objdump ranlib readelf size strings strip
%define binaries_binutils_comma %(echo %{binaries_binutils} | sed -e "s/ /,/g")

%description
This package is used in aarch64 architecture builds using qemu to speed up builds
with native binaries.
This should not be installed on systems, it is just intended for qemu environments.

%prep
%setup -q -D -T -n .

%build

%install
%if 0%{?use_cross_binaries}
%if 0%{?use_cross_nss}
binaries="%{_libdir}/libnsl.so.1 %{_libdir}/libnss_compat.so.2 %{_libdir}/rpm-plugins/msm.so" # loaded via dlopen by glibc
%endif # use_cross_nss
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
%endif # use_cross_binaries

# XXX this fails with the following error:
#     /opt/testing/bin/python: error while loading shared libraries: libpython2.7.so.1.0: wrong ELF class: ELFCLASS32

%if 0%{?use_cross_binaries}
%if 0%{?use_cross_ldso}
for executable in \
%if 0%{?use_cross_bash}
   /usr/bin/bash \
%endif # use_cross_bash
%if 0%{?use_cross_rpm}
   /usr/bin/{rpm,rpm2cpio,rpmdb,rpmkeys,rpmqpack,rpmbuild,rpmsign,rpmspec} \
   %{_libdir}/rpm-plugins/{exec.so,msm.so} \
   %{_libdir}/{libdb-4.8.so,libdb_cxx-4.8.so} \
%endif # use_cross_rpm
%if 0%{?use_cross_archivators}
   /usr/bin/{tar,gzip,bzip2,xz,xzdec} \
%endif # use_cross_archivators
%if 0%{?use_cross_stream_editors}
   /usr/bin/{grep,egrep,sed} \
%endif # use_cross_stream_editors
%if 0%{use_cross_nss}
%ifarch %ix86
   %{_libdir}/libnssdbm3.so %{_libdir}/libsoftokn3.so %{_libdir}/libfreebl3.so \
%else
   /usr/lib64/libnssdbm3.so /usr/lib64/libsoftokn3.so /lib64/libfreebl3.so \
%endif
%endif # use_cross_nss
%if 0%{?use_cross_coreutils}
   /usr/bin/{cat,expr,mkdir,mv,rm,rmdir} \
%endif # use_cross_coreutils
%if 0%{?use_cross_gettext_tools}
   /usr/bin/{msgexec,msgfmt,msgcat,msgmerge} \
%endif # use_cross_gettext_tools
%if 0%{use_cross_make}
   /usr/bin/make \
%endif # use_cross_make
%if 0%{?use_cross_m4}
   /usr/bin/m4 \
%endif # use_cross_m4
%if 0%{?use_cross_patch}
   /usr/bin/patch \
%endif # use_cross_patch
%if 0%{?use_cross_binutils}
   /usr/bin/aarch64-tizen-linux-{%{binaries_binutils_comma}} \
%endif
%if 0%{?use_cross_su}
   /usr/bin/su \
%endif
   $LD
do  
  binaries="$binaries $executable `ldd $executable | sed -n 's,.*=> \(/[^ ]*\) .*,\1,p'`"
done
%endif # use_cross_ldso
%endif # use_cross_binaries

%if %hijack_gcc

mkdir -p cross-compiler-tmp
for executable in $(tar -C cross-compiler-tmp -xvzf /usr/share/icecream-envs/cross-aarch64-gcc49-icecream-backend_*.tar.gz); do
    if [ ! -d "cross-compiler-tmp/$executable" ] ; then
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
tar xvz -C %buildroot%{our_path}/usr/share/icecream-envs/%{icecream_cross_env} -f /usr/share/icecream-envs/cross-aarch64-gcc49-icecream-backend_*.tar.gz
# It needs a tmp working directory which is writable
install -d -m0777 %buildroot%{our_path}/usr/share/icecream-envs
%endif

for binary in $binaries
do
  outfile=%buildroot%{our_path}$(echo $binary | sed 's:cross-compiler-tmp::;s:/opt/cross/aarch64-tizen-linux:/usr:')
  [ -f $outfile ] && continue
  mkdir -p ${outfile%/*}
  cp -aL $binary $outfile
  # XXX hack alert! Only works for aarch64-on-x86_64
%ifarch x86_64
  #[ "$(basename $outfile)" = "bash" ] && sed -i 's/x86_64/aarch64/g' "$outfile"
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

%if 0%{?use_cross_binaries}
# make gconv libraries available (needed for msg*)
%if 0%{?use_cross_gettext_tools}
%ifarch x86_64
mkdir -p %{buildroot}/usr/lib64/gconv
cp -a /usr/lib64/gconv/* "%{buildroot}/usr/lib64/gconv/"
%endif
%endif # use_cross_gettext_tools

# create symlinks for bash
%if 0%{?use_cross_bash}
mkdir -p "%{buildroot}%{our_path}/bin/"
mkdir -p "%{buildroot}%{our_path}/usr/bin/"
ln -sf ../usr/bin/bash "%{buildroot}%{our_path}/bin/sh"
ln -sf ../../bin/bash "%{buildroot}%{our_path}/usr/bin/sh"
%endif # use_cross_bash

# binutils needs to be exposed in /usr/bin
%if %{?use_cross_binutils}
if [ ! -d %{buildroot}%{our_path}/usr/aarch64-tizen-linux/bin ] ; then
  mkdir -p %{buildroot}%{our_path}/usr/aarch64-tizen-linux/bin
fi

for i in %{binaries_binutils} ; do
  if [ -f %{buildroot}%{our_path}/%{_bindir}/aarch64-tizen-linux-$i ] ; then
    mv %{buildroot}%{our_path}/%{_bindir}/aarch64-tizen-linux-$i %{buildroot}%{our_path}/usr/aarch64-tizen-linux/bin/$i
    if [ -f %{buildroot}%{our_path}/%{_bindir}/$i ] ; then
      rm %{buildroot}%{our_path}/%{_bindir}/$i
    fi
    ln -s ../aarch64-tizen-linux/bin/$i %{buildroot}%{our_path}/%{_bindir}/$i
    ln -s ../aarch64-tizen-linux/bin/$i %{buildroot}%{our_path}/%{_bindir}/aarch64-tizen-linux-$i
  fi
done
pushd %{buildroot}%{our_path} &&  ln -s usr/bin && popd
%endif # use_cross_binutils
%endif # use_cross_binaries

%if %hijack_gcc
# create symlinks for lib64 / lib mappings (gcc!)
mkdir -p "%{buildroot}%{our_path}/usr/lib/"
# binutils secondary directories
mkdir -p %{buildroot}%{our_path}/usr/aarch64-tizen-linux/
ln -sf ../bin %{buildroot}%{our_path}/usr/aarch64-tizen-linux/bin

%ifarch %ix86
ln -sf ../lib/gcc "%{buildroot}%{our_path}/usr/lib/gcc"
%else
ln -sf ../lib64/gcc "%{buildroot}%{our_path}/usr/lib/gcc"
%endif
# g++ can also be called c++
ln -sf g++ "%{buildroot}%{our_path}/usr/bin/c++"
# gcc can also be called cc
ln -sf gcc "%{buildroot}%{our_path}/usr/bin/cc"
# gcc can also be called gcc-4.8
ln -sf gcc "%{buildroot}%{our_path}/usr/bin/gcc-%{gcc_version}"

# nasty hack: If LIBRARY_PATH is set, native gcc adds the contents to its
#             library search list, but cross gcc does not. So switch to all
#             native in these situations.
for compiler in gcc g++
do
  mv %{buildroot}%{our_path}/usr/bin/${compiler}{,.real}
  echo '#!/bin/bash
  if [ "$LIBRARY_PATH" ]; then
    mv %{our_path}{,.bkp}
    exec /usr/bin/qemu-aarch64 /usr/bin/'${compiler}' "$@"
  fi
  exec -a /usr/bin/'${compiler}' %{our_path}/usr/bin/'${compiler}'.real "$@" -B%{our_path}/usr/aarch64-tizen-linux/bin -B%{our_path}/%{_libdir}/gcc/aarch64-tizen-linux/%{gcc_version}
  ' > %{buildroot}%{our_path}/usr/bin/${compiler}
  chmod +x %{buildroot}%{our_path}/usr/bin/${compiler}
done
#
# as is not writing right EABI ELF header inside of aarch64 environment for unknown reason
#
#mv %{buildroot}%{our_path}/usr/bin/as{,.real}
#echo '#!/bin/bash
#exec -a /usr/bin/as %{our_path}/usr/bin/as.real -meabi=5 "$@"
#' > %{buildroot}%{our_path}/usr/bin/as
#chmod +x %{buildroot}%{our_path}/usr/bin/as

# allow abuild to do the mv
chmod 777 %{buildroot}/emul

# make cross ld work with emulated compilers
rm %{buildroot}%{our_path}/usr/aarch64-tizen-linux/bin/ld.bfd
ln -s ./ld %{buildroot}%{our_path}/usr/aarch64-tizen-linux/bin/ld.bfd
mv %{buildroot}%{our_path}/usr/aarch64-tizen-linux/bin/ld{,.real}
echo '#!/bin/bash
if [ -n "$LD_LIBRARY_PATH" ]; then
  # arguments as file
  if [ "${1:0:1}" = "@" ]; then
    FILE="${1:1}"
    grep -v -- "--sysroot=" "$FILE" > "$FILE.fixed"
    mv "$FILE.fixed" "$FILE"
  fi

  # cross ld does not work correctly using LD_LIBRARY_PATH, use aarch64 version
  args=()
  for i in "$@"; do
    if [ "${i:0:10}" != "--sysroot=" ]; then
      args=(${args[@]} "$i")
    fi
  done
  exec /usr/bin/qemu-aarch64 /usr/bin/ld "${args[@]}"
fi
for i in "$@"; do
  if [ "${i:0:10}" = "--sysroot=" ]; then
    exec -a "$0" %{our_path}/usr/aarch64-tizen-linux/bin/ld.real "$@"
  fi
done

exec -a "$0" %{our_path}/usr/aarch64-tizen-linux/bin/ld.real --sysroot=/ "$@"
' > %{buildroot}%{our_path}/usr/aarch64-tizen-linux/bin/ld
chmod +x %{buildroot}%{our_path}/usr/aarch64-tizen-linux/bin/ld

# To support gcc sysroot
mkdir -p %{buildroot}/usr/aarch64-tizen-linux
ln -sf .. %{buildroot}/usr/aarch64-tizen-linux/usr
ln -sf ../include %{buildroot}/usr/aarch64-tizen-linux/include
%endif # hijack_gcc

# Make QEMU available through /qemu
mkdir %buildroot/qemu
cp -L /usr/bin/qemu-aarch64 %buildroot/qemu/
mkdir -p %buildroot/usr/bin/

cp /usr/bin/qemu-aarch64-binfmt %buildroot/usr/bin/qemu-arm64-binfmt
ln -sf /qemu/qemu-aarch64 %buildroot/usr/bin/qemu-arm64
ln -sf /qemu/qemu-aarch64 %buildroot/usr/bin/qemu-aarch64
ln -sf /qemu/qemu-aarch64 %buildroot/qemu/qemu-arm64
ln -sf /usr/bin/qemu-arm64-binfmt %buildroot/qemu/qemu-arm64-binfmt
ln -sf /usr/bin/qemu-arm64-binfmt %buildroot/qemu/qemu-aarch64-binfmt

%fdupes -s %{buildroot}

export NO_BRP_CHECK_RPATH="true"

# Fix variable in baselibs 
%if 0%{?use_binfmt_binary}
sed -e '/use_binfmt_binary/s/.*/\tpost "%%if 1"/' -i %{_sourcedir}/baselibs.conf
%else
sed -e '/use_binfmt_binary/s/.*/\tpost "%%if 0"/' -i %{_sourcedir}/baselibs.conf
%endif

rm -rf %{buildroot}/%{our_path}/bin
ln -s %{our_path}/usr/bin %{buildroot}/%{our_path}/bin
rm -rf %{buildroot}/%{our_path}/sbin
ln -s %{our_path}/usr/sbin %{buildroot}/%{our_path}/sbin

%if 0%{?use_cross_rpm}
ln -s %{our_path}/usr/bin/rpm %{buildroot}/%{our_path}/usr/bin/rpmquery
ln -s %{our_path}/usr/bin/rpm %{buildroot}/%{our_path}/usr/bin/rpmverify
%endif # use_cross_rpm

%post
if [ $(uname -m) = aarch64 ]; then
    builtin echo "aarch64 arch"
    # XXX find a way around this for cross-gcc
    mkdir -p /usr/lib64/gcc /lib64 || true
    ln -sf ../../lib/gcc/aarch64-tizen-linux /usr/lib64/gcc/aarch64-tizen-linux || true
    ln -sf %{our_path}/lib64/libnsl.so.1 /lib64/libnsl.so.1 || true
	mkdir -p /qemu
	ln -sf /emul/i586-for-aarch64/lib/ld-linux.so.2 /lib
	#ln -sf /usr/bin/qemu-aarch64 /qemu/qemu-aarch64-binfmt
	echo '/opt/testing/lib/' >> /etc/ld.so.conf
fi
# use qemu-aarch64{,-binfmt} from a  safe directory, so even overwriting
# /usr/bin/$file won't affect our ability to run aarch64 code

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

builtin echo "Registering accelerated handler"
if [ -e /proc/sys/fs/binfmt_misc/aarch64 ]; then
    builtin echo -1 > /proc/sys/fs/binfmt_misc/aarch64
fi

builtin echo ':aarch64:M::\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\xb7:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff:/qemu/qemu-aarch64:OC' > /proc/sys/fs/binfmt_misc/register
cat /proc/sys/fs/binfmt_misc/aarch64

if [ $did_mount_it ]; then 
builtin echo "Unmounting again.";
umount /proc/sys/fs/binfmt_misc
fi

builtin echo "All done"

# Fix up sysroot paths
rm -rf /usr/aarch64-tizen-linux/lib
ln -s /lib /usr/aarch64-tizen-linux/usr/lib

%files
%defattr(-,root,root)  
%if 0%{?use_cross_binaries}
%if 0%{?hijack_gcc}
%dir /usr/aarch64-tizen-linux
/usr/aarch64-tizen-linux/usr
/usr/aarch64-tizen-linux/include
%endif # hijack_gcc
%if 0%{?use_cross_ldso}
/emul
%endif # use_cross_ldso
%endif # use_cross_binaries
/qemu
/usr/bin/qemu-arm64-binfmt
/usr/bin/qemu-arm64
/usr/bin/qemu-aarch64
%ifarch x86_64
/usr/lib64
%endif

%changelog
