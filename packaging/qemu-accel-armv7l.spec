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

%define emulated_arch_long armv7l
%define emulated_arch_short arm
%define emulated_arch_synonim arm
%define emulated_arch_triple_short %{emulated_arch_short}-tizen-linux-gnueabi
%define emulated_arch_triple_long %{emulated_arch_long}-tizen-linux-gnueabi

# Check whether macro "gcc_version" was defined via project config
%if 0%{?gcc_version}
%else
# If the macro was undefined, set it to this default value:
%define gcc_version 49
%endif
%{expand:%%define gcc_version_dot %(echo -n "%{gcc_version}" | sed -e "s/\([0-9]\)\([0-9]\)/\1.\2/g")}

# Choose which gcc hijack method (if any) to use.
# Only select one of the two at a time!
%define hijack_gcc 1


Name:           qemu-accel-%{emulated_arch_long}
Version:        0.4
Release:        0
AutoReqProv:    off
Source0:		ld-wrapper.sh
Source1:		gcc-wrapper.sh
BuildRequires:  cross-%{emulated_arch_short}-binutils
BuildRequires:  cross-%{emulated_arch_short}-binutils-gold
%if %hijack_gcc
BuildRequires:  cross-%{emulated_arch_long}-gcc%{gcc_version}-icecream-backend
%endif
#BuildRequires:  expect
BuildRequires:  fdupes
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
Summary:        Native binaries for speeding up cross compile
License:        GPL-2.0
Group:          Development/Cross Compilation
ExclusiveArch:  x86_64 %ix86


# default path in qemu
%define HOST_ARCH %(echo -n "%{_host_cpu}" | sed -e "s/i.86/i586/;s/ppc/powerpc/;s/sparc64.*/sparc64/;s/sparcv.*/sparc/;")
%define our_path /emul/%{HOST_ARCH}-for-%{emulated_arch_short}
%ifarch %ix86
%define icecream_cross_env cross-%{emulated_arch_long}-gcc%{gcc_version}-icecream-backend_i386
%else
%define icecream_cross_env cross-%{emulated_arch_long}-gcc%{gcc_version}-icecream-backend_x86_64
%endif
%define binaries_binutils addr2line ar as elfedit gprof ld ld.bfd ld.gold nm objcopy objdump ranlib readelf size strings strip
%define binaries_binutils_comma %(echo %{binaries_binutils} | sed -e "s/ /,/g")

%description
This package is used in %{emulated_arch_long} architecture builds using qemu to speed up builds
with native binaries.
This should not be installed on systems, it is just intended for qemu environments.

%prep

%build

%install
binaries="%{_libdir}/libnsl.so.1 %{_libdir}/libnss_compat.so.2 %{_libdir}/rpm-plugins/msm.so" # loaded via dlopen by glibc
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
   /usr/bin/bash \
   /usr/bin/{rpm,rpm2cpio,rpmdb,rpmkeys,rpmqpack,rpmbuild,rpmsign,rpmspec} \
   %{_libdir}/rpm-plugins/{exec.so,msm.so} \
   %{_libdir}/{libdb-4.8.so,libdb_cxx-4.8.so} \
   /usr/bin/{tar,gzip,bzip2,xz,xzdec} \
   /usr/bin/{grep,egrep,sed} \
%ifarch %ix86
   %{_libdir}/libnssdbm3.so %{_libdir}/libsoftokn3.so %{_libdir}/libfreebl3.so \
%else
   /usr/lib64/libnssdbm3.so /usr/lib64/libsoftokn3.so /lib64/libfreebl3.so \
%endif
   /usr/bin/{cat,expr,mkdir,mv,rm,rmdir} \
   /usr/bin/{msgexec,msgfmt,msgcat,msgmerge} \
   /usr/bin/make \
   /usr/bin/m4 \
   /usr/bin/patch \
   /usr/bin/%{emulated_arch_triple_short}-{%{binaries_binutils_comma}}
do
  binaries="$binaries $executable `ldd $executable | sed -n 's,.*=> \(/[^ ]*\) .*,\1,p'`"
done

%if %hijack_gcc
# extract cross-compiler
mkdir -p cross-compiler-tmp
for executable in $(tar -C cross-compiler-tmp -xvzf /usr/share/icecream-envs/cross-%{emulated_arch_long}-gcc%{gcc_version}-icecream-backend_*.tar.gz); do
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
tar xvz -C %buildroot%{our_path}/usr/share/icecream-envs/%{icecream_cross_env} -f /usr/share/icecream-envs/cross-%{emulated_arch_long}-gcc%{gcc_version}-icecream-backend_*.tar.gz
# It needs a tmp working directory which is writable
install -d -m0755 %buildroot%{our_path}/usr/share/icecream-envs
%endif

for binary in $binaries
do
  outfile=%buildroot%{our_path}$(echo $binary | sed 's:cross-compiler-tmp::;s:/opt/cross/%{emulated_arch_triple_long}:/usr:')
  [ -f $outfile ] && continue
  mkdir -p ${outfile%/*}
  cp -aL $binary $outfile
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
mkdir -p "%{buildroot}%{our_path}/bin/"
mkdir -p "%{buildroot}%{our_path}/usr/bin/"
ln -sf ../usr/bin/bash "%{buildroot}%{our_path}/bin/sh"
ln -sf ../../bin/bash "%{buildroot}%{our_path}/usr/bin/sh"

# binutils needs to be exposed in /usr/bin
if [ ! -d %{buildroot}%{our_path}/usr/%{emulated_arch_triple_short}/bin ] ; then
  mkdir -p %{buildroot}%{our_path}/usr/%{emulated_arch_triple_short}/bin
fi

for i in %{binaries_binutils} ; do
  if [ -f %{buildroot}%{our_path}/%{_bindir}/%{emulated_arch_triple_short}-$i ] ; then
    mv %{buildroot}%{our_path}/%{_bindir}/%{emulated_arch_triple_short}-$i %{buildroot}%{our_path}/usr/%{emulated_arch_triple_short}/bin/$i
    if [ -f %{buildroot}%{our_path}/%{_bindir}/$i ] ; then
      rm %{buildroot}%{our_path}/%{_bindir}/$i
    fi
    ln -s ../%{emulated_arch_triple_short}/bin/$i %{buildroot}%{our_path}/%{_bindir}/$i
    ln -s ../%{emulated_arch_triple_short}/bin/$i %{buildroot}%{our_path}/%{_bindir}/%{emulated_arch_triple_short}-$i
  fi
done
pushd %{buildroot}%{our_path} &&  ln -s usr/bin && popd

%if %hijack_gcc
# create symlinks for lib64 / lib mappings (gcc!)
mkdir -p "%{buildroot}%{our_path}/usr/lib/"
# binutils secondary directories
mkdir -p %{buildroot}%{our_path}/usr/%{emulated_arch_triple_long}/
ln -sf ../bin %{buildroot}%{our_path}/usr/%{emulated_arch_triple_long}/bin

%ifarch %ix86
ln -sf ../lib/gcc "%{buildroot}%{our_path}/usr/lib/gcc"
%else
ln -sf ../lib64/gcc "%{buildroot}%{our_path}/usr/lib/gcc"
%endif

# Enable wrapper for GCC compiler:
mv %{buildroot}%{our_path}/usr/bin/gcc{,.real}
mv %{buildroot}%{our_path}/usr/bin/g++{,.real}
cp %{SOURCE1} %{buildroot}%{our_path}/usr/bin/gcc-wrapper.sh
chmod 755 %{buildroot}%{our_path}/usr/bin/gcc-wrapper.sh

# Create symlinks for different synonims of compiler names:
for compiler in gcc cc g++ c++ ; do
  ln -sf gcc-wrapper.sh %{buildroot}%{our_path}/usr/bin/${compiler}
  ln -sf gcc-wrapper.sh %{buildroot}%{our_path}/usr/bin/${compiler}-%{gcc_version_dot}
  ln -sf ${compiler}.real %{buildroot}%{our_path}/usr/bin/${compiler}-%{gcc_version_dot}.real
done
# g++ can also be called c++
ln -sf g++.real "%{buildroot}%{our_path}/usr/bin/c++.real"
# gcc can also be called cc
ln -sf gcc.real "%{buildroot}%{our_path}/usr/bin/cc.real"


# allow abuild to do the mv
chmod 755 %{buildroot}/emul

# make cross ld work with emulated compilers
cp %{SOURCE0} %{buildroot}%{our_path}/usr/%{emulated_arch_triple_short}/bin/ld-wrapper.sh
for LD_NAME in ld ld.gold ; do
  mv %{buildroot}%{our_path}/usr/%{emulated_arch_triple_short}/bin/${LD_NAME}{,.real}
  ln -s ld-wrapper.sh %{buildroot}%{our_path}/usr/%{emulated_arch_triple_short}/bin/${LD_NAME}
done

# Write config that will be used by wrappers at run-time.
echo '
QEMU_NAME=/usr/bin/qemu-arm
CROSS_ACCELERATION_DIRECTORY=%{our_path}
GCC_LIBEXEC_DIRECTORY=%{_libdir}/gcc/%{emulated_arch_triple_long}/%{gcc_version_dot}
CROSS_BIN_PREFIX=/usr/%{emulated_arch_triple_short}/bin
' > %{buildroot}%{our_path}/usr/%{emulated_arch_triple_short}/bin/wrapper-config.sh

chmod 755 %{buildroot}%{our_path}/usr/%{emulated_arch_triple_short}/bin/ld-wrapper.sh

# To support gcc sysroot
mkdir -p %{buildroot}/usr/%{emulated_arch_triple_long}
ln -sf .. %{buildroot}/usr/%{emulated_arch_triple_long}/usr
ln -sf ../include %{buildroot}/usr/%{emulated_arch_triple_long}/include
%endif

# Make QEMU available through /qemu
mkdir %buildroot/qemu
cp -L /usr/bin/qemu-%{emulated_arch_short}{,-binfmt} %buildroot/qemu/
mkdir -p %buildroot/usr/bin/

if [[ %{emulated_arch_short} != %{emulated_arch_synonim} ]] ; then
  ln -sf /qemu/qemu-%{emulated_arch_short} %buildroot/qemu/qemu-%{emulated_arch_synonim}
  ln -sf /qemu/qemu-%{emulated_arch_short}-binfmt %buildroot/qemu/qemu-%{emulated_arch_synonim}-binfmt
fi


export NO_BRP_CHECK_RPATH="true"

rm -rf %{buildroot}/%{our_path}/bin
ln -s %{our_path}/usr/bin %{buildroot}/%{our_path}/bin
rm -rf %{buildroot}/%{our_path}/sbin
ln -s %{our_path}/usr/sbin %{buildroot}/%{our_path}/sbin

ln -s %{our_path}/usr/bin/rpm %{buildroot}/%{our_path}/usr/bin/rpmquery
ln -s %{our_path}/usr/bin/rpm %{buildroot}/%{our_path}/usr/bin/rpmverify

%post
ldconfig

%postun
ldconfig

%files
%defattr(-,root,root)
%dir /usr/%{emulated_arch_triple_long}
/usr/%{emulated_arch_triple_long}/usr
/usr/%{emulated_arch_triple_long}/include
/emul
/qemu
%ifarch x86_64
/usr/lib64/*
%endif

%changelog
