%define cross aarch64
%define aarch64 1

#
# spec file for package qemu-accel-ARCH, where ARCH = armv7l or aarch64
#
# Copyright (c) 2012 SUSE LINUX Products GmbH, Nuernberg, Germany.
# Copyright (c) 2015 Tizen
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.tizen.org/
#


# arm
%define target_cpu %{cross}
%define target_abi %{?armv7l:eabi}
%define target_arch %{target_cpu}-tizen-linux-gnu%{?target_abi}
%define libdir %{_prefix}/lib%{?aarch64:64}

# default path in qemu
%define our_path /emul

Name:           qemu-accel
Version:        0.4
Release:        0
AutoReqProv:    off
BuildRequires:  gcc-%{cross}
BuildRequires:  binutils-%{cross}
#BuildRequires:  expect
BuildRequires:  fdupes
BuildRequires:  gettext-runtime
BuildRequires:  gettext-tools
BuildRequires:  m4
# required for xxd
BuildRequires:  vim
BuildRequires:  patchelf
BuildRequires:  rpmlint-mini
BuildRequires:  rpmlint-tizen
BuildRequires:  elfutils
BuildRequires:  libxslt-tools
BuildRequires:  cmake
BuildRequires:  gawk
BuildRequires:  libstdc++
BuildRequires:  python
BuildRequires:  python-xml
BuildRequires:  python-magic
BuildRequires:  python-rpm
BuildRequires:  file
BuildRequires:  libasan
Summary:        Native binaries for speeding up cross compile
License:        GPL-2.0
Group:          Development/Cross Compilation
ExclusiveArch:  x86_64 %{ix86}


%description
This package is used in %{cross} architecture builds using qemu to speed up builds
with native binaries.
This should not be installed on systems, it is just intended for qemu environments.

%package -n python-accel
Version: %{version}
Release: %{release}
Summary: Binaries for python acceleration
License:        GPL-2.0
Group:          Development/Cross Compilation

%description -n python-accel
This package is used in qemu-accel to accelerate python.

%prep

%build

%install
set +x
gcc_version=`gcc --version | sed -ne '1s/[^0-9]*\(\([0-9]\.\?\)*\).*/\1/p'`
# just like it is determided in python.spec
python_version=`python --version 2>&1 | sed -ne '1s/.* //p' | head -c 3`

binaries="%{_libdir}/libnsl.so.1 %{_libdir}/libnss_compat.so.2" # loaded via dlopen by glibc
%ifarch %ix86
  LD="/%{_lib}/ld-linux.so.2"
%endif
%ifarch x86_64
  LD="/%{_lib}/ld-linux-x86-64.so.2"
%endif

# Check if we use toolchain with sanitizers support
[ -f /usr/bin/gcc-force-options ] && sanitizer_enabled=1
if [ x"$sanitizer_enabled" == x"1" ]; then
   real_compiler=`find %{_bindir} -name '*-real' -printf '%{_bindir}/%%f '`
fi

for executable in $LD \
   %{_bindir}/bash \
   %{_bindir}/{rpm,rpm2cpio,rpmdb,rpmkeys,rpmqpack,rpmbuild,rpmsign,rpmspec} \
   %{_libdir}/rpm-plugins/exec.so \
   %{_libdir}/{libdb-4.8.so,libdb_cxx-4.8.so} \
   %{_bindir}/{tar,gzip,bzip2,xz,xzdec} \
   %{_bindir}/{grep,sed} \
   %{_libdir}/libnssdbm3.so %{_libdir}/libsoftokn3.so %{_libdir}/libfreebl3.so \
   %{_libdir}/lib*san.so* \
   %{_bindir}/{cat,expr,mkdir,mv,rm,rmdir} \
   %{_bindir}/{msgexec,msgfmt,msgcat,msgmerge} \
   %{_bindir}/make \
   %{_bindir}/m4 \
   %{_bindir}/{awk,gawk} \
   %{_bindir}/patch \
   %{_bindir}/diff \
   %{_bindir}/echo \
   %{_bindir}/head \
   %{_bindir}/eu-{addr2line,ar,elfcmp,elflint,findtextrel,ld,nm,objdump,ranlib,readelf,size,strings,strip,unstrip} \
   %{_bindir}/xsltproc \
   %{_bindir}/python${python_version} \
   %{_libdir}/python${python_version}/lib-dynload/*.so \
   %{_libdir}/python${python_version}/site-packages/*/*.so \
   %{_bindir}/{ccmake,cmake,cpack,ctest} \
   %{_bindir}/%{target_arch}-{addr2line,ar,as,c++filt,dwp,elfedit,gprof,ld,ld.bfd,ld.gold,nm,objcopy,objdump,ranlib,readelf,size,strings,strip} \
   %{_bindir}/%{target_arch}-{c++,g++,cpp,gcc,gcc-${gcc_version},gcc-ar,gcc-nm,gcc-ranlib,gcov} \
   %{libdir}/gcc/%{target_arch}/${gcc_version}/{cc1,cc1plus,collect2,lto1,lto-wrapper,liblto_plugin.so} \
   %{_bindir}/file \
   ${real_compiler} \
   %{_bindir}/{find,xargs,readlink,ls}
do
  binaries="$binaries $executable `ldd $executable | sed -n 's,.*=> \(/[^ ]*\) .*,\1,p'`"
done

## dump list of binaries and list of packages
echo "### binaries to accelerate ###"
echo $binaries | sed -e 's/[^ ]*\///g;s/[^ ]*.so[^ ]* \?//g'
echo "### packages that are used ###"
for bin in $binaries
do
  rpm -qf $bin
done | grep -v "not owned" | sed -e "s/-[0-9].*//g" | sort -u
echo ""


for binary in $binaries
do
  # We don't need to accelerate shell scripts
  filetype=`file --brief $binary`
  [[ x"$filetype" == x"POSIX shell script"* ]] && continue

  outfile=%{buildroot}/%{our_path}/$binary
  [ ! -e $binary ] && echo "WARNING: File '${binary}' not found, ignoring" && continue
  [ -f $outfile ] && echo "WARNING: File '${outfile}' exists, ignoring" && continue
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
  patchelf --set-rpath "%{our_path}/%{libdir}" $outfile
# not all binaries have an .interp section
  if patchelf --print-interpreter $outfile 1>/dev/null 2>/dev/null; then
    patchelf --set-interpreter %{our_path}$LD $outfile
  fi
done

# create symlinks for bash
ln -s usr/bin "%{buildroot}%{our_path}/bin"
ln -sf bash "%{buildroot}%{our_path}/usr/bin/sh"

# move everything into single usr/lib
mkdir -p %{buildroot}%{our_path}/usr/lib_new
if [ ! "%{_libdir}" == "%{libdir}" ]; then
  rm -rf %{buildroot}%{our_path}%{_libdir}/gcc
fi
for dir in /usr/lib /usr/lib64 /lib64 /lib; do
  [ -d "%{buildroot}%{our_path}$dir" ] || continue
  mv %{buildroot}%{our_path}$dir/* %{buildroot}%{our_path}/usr/lib_new
done
rm -rf %{buildroot}%{our_path}/{usr/lib64,usr/lib,lib64,lib}
mv %{buildroot}%{our_path}/usr/lib_new %{buildroot}%{our_path}/usr/lib
ln -s lib %{buildroot}%{our_path}/usr/lib64
ln -s usr/lib %{buildroot}%{our_path}/lib64
ln -s usr/lib %{buildroot}%{our_path}/lib

# rename binutils binaries
for binary in addr2line ar as c++filt dwp elfedit gprof ld ld.bfd ld.gold nm objcopy objdump ranlib readelf size strings strip
do
  mv %{buildroot}%{our_path}%{_bindir}/%{target_arch}-$binary %{buildroot}%{our_path}%{_bindir}/$binary
done

mkdir -p %{buildroot}/%{our_path}/%{_prefix}/%{target_arch}/bin
for binary in ar as ld{,.bfd,.gold} nm obj{copy,dump} ranlib strip; do
  ln -sf %{our_path}%{_bindir}/$binary %{buildroot}%{our_path}%{_prefix}/%{target_arch}/bin/$binary
done

# create symlinks for python
mv %{buildroot}%{our_path}%{_bindir}/python${python_version} %{buildroot}%{our_path}%{_bindir}/python${python_version}.orig
cat > %{buildroot}%{our_path}%{_bindir}/python${python_version} << EOF
#!/bin/bash
if [ -z "\$PYTHONPATH" ]; then
  export PYTHONPATH="%{libdir}/python${python_version}"
else
  export PYTHONPATH+=":%{libdir}/python${python_version}"
fi
export PYTHONHOME="%{our_path}%{_prefix}"
%{our_path}%{_bindir}/python${python_version}.orig "\$@"
EOF
chmod +x %{buildroot}%{our_path}%{_bindir}/python${python_version}

ln -s python${python_version} %{buildroot}%{our_path}%{_bindir}/python
ln -s python${python_version} %{buildroot}%{our_path}%{_libdir}/python

# rpmlint acceleration
mkdir -p %{buildroot}%{our_path}/opt/testing/bin
cp %{buildroot}%{our_path}%{_bindir}/python${python_version}.orig %{buildroot}%{our_path}/opt/testing/bin/
cat > %{buildroot}%{our_path}/opt/testing/bin/python${python_version} << EOF
#!/bin/bash
if [ -z "\$PYTHONPATH" ]; then
  export PYTHONPATH="%{libdir}/python${python_version}"
else
  export PYTHONPATH+=":%{libdir}/python${python_version}"
fi
export PYTHONHOME="%{our_path}%{_prefix}"
%{our_path}/opt/testing/bin/python${python_version}.orig "\$@"
EOF
chmod +x %{buildroot}%{our_path}/opt/testing/bin/python${python_version}
ln -s python${python_version} %{buildroot}%{our_path}/opt/testing/bin/python

mkdir -p %{buildroot}%{our_path}%{_libdir}/python${python_version}/site-packages/rpm/
mkdir -p %{buildroot}%{our_path}%{_libdir}/python${python_version}/encodings/
cp %{_libdir}/python${python_version}/site-packages/rpm/*.py %{buildroot}%{our_path}%{_libdir}/python${python_version}/site-packages/rpm/
cp %{_libdir}/python${python_version}/*.py %{buildroot}%{our_path}%{_libdir}/python${python_version}/
cp %{_libdir}/python${python_version}/encodings/*.py %{buildroot}%{our_path}%{_libdir}/python${python_version}/encodings/


# rename gcc binaries
for bin in c++ g++ gcc
do
  [ x"$sanitizer_enabled" == x"1" ] && bin+="-real"
  mv %{buildroot}%{our_path}%{_bindir}/%{target_arch}-$bin %{buildroot}/%{our_path}%{_bindir}/$bin
  ln -s $bin %{buildroot}%{our_path}%{_bindir}/%{target_arch}-$bin
done
for bin in cpp gcc-ar gcc-nm gcc-ranlib
do
  mv %{buildroot}%{our_path}%{_bindir}/%{target_arch}-$bin %{buildroot}/%{our_path}%{_bindir}/$bin
  ln -s $bin %{buildroot}%{our_path}%{_bindir}/%{target_arch}-$bin
done
mv %{buildroot}%{our_path}%{_bindir}/%{target_arch}-gcov %{buildroot}%{our_path}%{_bindir}/gcov
ln -s gcc %{buildroot}%{our_path}/%{_bindir}/cc

# rpmbuild when generating 'requires' tag for gobject-introspection binaries
# selects (64-bit) suffix for libs based on ${HOSTTYPE} bash variable
# so we replace x86_64 to armv7l to avoid bogus dependencies
%ifarch x86_64
%{?armv7l:
sed -i -e "s/x86_64/armv7l/g" %{buildroot}%{our_path}%{_bindir}/bash
}
%endif

# create symlinks for gcc build (CC_FOR_TARGET)
mkdir -p %{buildroot}%{our_path}/home/abuild/rpmbuild/BUILD/gcc-${gcc_version}/obj/gcc
for binary in as cpp gcc-ar gcc-nm gcc-ranlib gcov nm
do
  ln -sf %{our_path}%{_bindir}/${binary} %{buildroot}%{our_path}/home/abuild/rpmbuild/BUILD/gcc-${gcc_version}/obj/gcc/${binary}
done
for binary in cc1 cc1plus collect2 lto1 lto-wrapper
do
  ln -sf %{our_path}/usr/lib/gcc/%{target_arch}/${gcc_version}/${binary} %{buildroot}%{our_path}/home/abuild/rpmbuild/BUILD/gcc-${gcc_version}/obj/gcc/${binary}
done
ln -sf %{our_path}%{_bindir}/gcc %{buildroot}%{our_path}/home/abuild/rpmbuild/BUILD/gcc-${gcc_version}/obj/gcc/xgcc
ln -sf %{our_path}%{_bindir}/g++ %{buildroot}%{our_path}/home/abuild/rpmbuild/BUILD/gcc-${gcc_version}/obj/gcc/xg++

# support /lib/cpp
ln -sf %{our_path}%{_bindir}/cpp %{buildroot}%{our_path}/usr/lib/cpp

set -x
# update baselibs.conf, overwrite LTO plugin
sed -i -e "s,#PLUGIN_POSTIN#,ln -sf %{our_path}%{_libdir}/gcc/%{target_arch}/${gcc_version}/liblto_plugin.so %{libdir}/gcc/%{target_arch}/${gcc_version}/liblto_plugin.so," %{_sourcedir}/baselibs.conf
sed -i -e "s,#PLUGIN_POSTUN#,ln -sf liblto_plugin.so.0 %{libdir}/gcc/%{target_arch}/${gcc_version}/liblto_plugin.so," %{_sourcedir}/baselibs.conf

# allow build of baselibs.conf
sed -i -e "/targettype %{cross} block!/d" %{_sourcedir}/baselibs.conf

%post
ldconfig

%postun
ldconfig


%files
%defattr(-,root,root)
%{our_path}
%exclude %{our_path}%{_bindir}/python*

%files -n python-accel
%defattr(-,root,root)
%{our_path}%{_bindir}/python*

%changelog
