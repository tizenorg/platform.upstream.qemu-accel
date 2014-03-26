#
# spec file for package qemu-accel-armv7el
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
%define use_icecream 0
%define hijack_gcc 1

Name:           qemu-accel-armv7el
Version:        0.2
Release:        0
AutoReqProv:    off
BuildRequires:  cross-arm-binutils
BuildRequires:  cross-armv7el-gcc47-icecream-backend
#BuildRequires:  expect
BuildRequires:  fdupes
BuildRequires:	glibc-locale
BuildRequires:  gcc-c++
BuildRequires:  gettext-runtime
BuildRequires:  gettext-tools
BuildRequires:  m4
# required for xxd
BuildRequires:  vim
BuildRequires:  patchelf
#BuildRequires:  rpmlint-mini
BuildRequires:  qemu-linux-user
%if %use_icecream
BuildRequires:  icecream
BuildRequires:  schroot
%endif
Requires:       coreutils
Summary:        Native binaries for speeding up cross compile
License:        GPL-2.0
Group:          Development/Libraries/Cross
ExclusiveArch:  x86_64

# default path in qemu
%define HOST_ARCH %(echo %{_host_cpu} | sed -e "s/i.86/i586/;s/ppc/powerpc/;s/sparc64.*/sparc64/;s/sparcv.*/sparc/;")
%define our_path /emul/%{HOST_ARCH}-for-arm
%define icecream_cross_env cross-armv7el-gcc47-icecream-backend_x86_64

%description
This package is used in armv7el architecture builds using qemu to speed up builds
with native binaries.
 This should not be installed on systems, it is just intended for qemu environments.

%prep
%setup -q -D -T -n .

%build

%install
binaries="/%_lib/libnsl.so.1 /%_lib/libnss_compat.so.2" # loaded via dlopen by glibc
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
   /bin/{bash,grep,egrep,gzip,sed,tar,rpm} \
   /usr/lib64/libnssdbm3.so /usr/lib64/libsoftokn3.so /lib64/libfreebl3.so \
   /usr/bin/{bzip2,cat,expr,make,m4,mkdir,msgexec,msgfmt,msgcat,msgmerge,mv,patch,rm,rmdir,rpmbuild,xz,xzdec} \
%if %use_icecream
   /usr/sbin/iceccd /usr/bin/icecc /usr/bin/schroot \
%endif
   /usr/arm-tizen-linux-gnueabi/bin/{as,ar,ld,ld.bfd,objcopy,objdump}
do  
  binaries="$binaries $executable `ldd $executable | sed -n 's,.*=> \(/[^ ]*\) .*,\1,p'`"
done

%if %hijack_gcc
# extract cross-compiler
mkdir -p cross-compiler-tmp
for executable in $(tar -C cross-compiler-tmp -xvzf /usr/share/icecream-envs/cross-armv7el-gcc47-icecream-backend_*.tar.gz); do
    if [ ! -d "cross-compiler-tmp/$executable" ]; then
        binaries="$binaries cross-compiler-tmp/$executable"
    fi
done
%endif

%if %use_icecream
mkdir -p %buildroot%{our_path}/opt/icecream/bin
mkdir -p %buildroot/opt/icecream/bin
for p in gcc g++ cc c++ ; do
    ln -s %{our_path}/usr/bin/icecc %buildroot%{our_path}/opt/icecream/bin/$p
    echo "#!/bin/bash
exec /usr/bin/$p \"\$@\"" > %buildroot/opt/icecream/bin/$p
    chmod a+x %buildroot/opt/icecream/bin/$p
done
# to have it in the $PATH
ln -s %{our_path}/usr/bin/schroot %buildroot/opt/icecream/bin/schroot
mkdir -p %buildroot/etc/schroot/chroot.d
mkdir -p %buildroot/%_lib/security

# unfortunately pam does not look for emul (yet)
# as soon as we have lib64 in arm, we're doomed :)
cp /lib64/security/pam_permit.so %buildroot/%_lib/security
mkdir -p %buildroot/etc/pam.d/
for i in auth session account password session; do 
  echo "$i    optional  pam_permit.so" >> %buildroot/etc/pam.d/schroot
done

# Install 
mkdir -p %buildroot/usr/share/icecream-envs/%{icecream_cross_env}
pushd %buildroot/usr/share/icecream-envs/%{icecream_cross_env}
tar xvf /usr/share/icecream-envs/%{icecream_cross_env}.tar.gz
mkdir tmp
chmod a+w tmp
popd
mkdir -p %{buildroot}/etc/profile.d
echo "export ICECC_SCHROOT=cross"          >  %{buildroot}/etc/profile.d/icecream.sh
echo "export ICECC_CC=/usr/bin/gcc-4.7"    >> %{buildroot}/etc/profile.d/icecream.sh
echo "export ICECC_CXX=/usr/bin/g++-4.7"   >> %{buildroot}/etc/profile.d/icecream.sh
echo "#export ICECC_DEBUG=debug"           >> %{buildroot}/etc/profile.d/icecream.sh
echo 'export PATH=/opt/icecream/bin:$PATH' >> %{buildroot}/etc/profile.d/icecream.sh

mkdir -p %{buildroot}/etc/schroot
( 
echo "[cross]" 
echo "directory=/usr/share/icecream-envs/%{icecream_cross_env}" 
echo "users=abuild"
) > %{buildroot}/etc/schroot/schroot.conf
%endif

%if %hijack_gcc
# Install 
mkdir -p %buildroot%{our_path}/usr/share/icecream-envs/%{icecream_cross_env}
cp -a /usr/share/icecream-envs/%{icecream_cross_env}.tar.gz \
      %buildroot%{our_path}/usr/share/icecream-envs
# And extract it for direct usage
tar xvz -C %buildroot%{our_path}/usr/share/icecream-envs/%{icecream_cross_env} -f /usr/share/icecream-envs/cross-armv7el-gcc47-icecream-backend_*.tar.gz
# It needs a tmp working directory which is writable
install -d -m0777 %buildroot%{our_path}/usr/share/icecream-envs
%endif

for binary in $binaries
do
  outfile=%buildroot%{our_path}$(echo $binary | sed 's:cross-compiler-tmp::;s:/opt/cross/armv7el-tizen-linux-gnueabi:/usr:')
  [ -f $outfile ] && continue
  mkdir -p ${outfile%/*}
  cp -aL $binary $outfile
  # XXX hack alert! Only works for armv7l-on-x86_64
  [ "$(basename $outfile)" = "bash" ] && sed -i 's/x86_64/armv7l/g' "$outfile"
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
mkdir -p %{buildroot}/usr/lib64/gconv
cp -a /usr/lib64/gconv/* "%{buildroot}/usr/lib64/gconv/"

# create symlinks for bash
ln -sf bash "%{buildroot}%{our_path}/bin/sh"
ln -sf ../../bin/bash "%{buildroot}%{our_path}/usr/bin/sh"
# create symlink for gzip
ln -sf ../../bin/gzip "%{buildroot}%{our_path}/usr/bin/gzip"
ln -sf ../../bin/sed "%{buildroot}%{our_path}/usr/bin/sed"

# binutils needs to be exposed in /usr/bin
for i in ar ld ld.bfd objcopy objdump; do
  ln -s ../arm-tizen-linux-gnueabi/bin/$i %{buildroot}%{our_path}/usr/bin/$i
done

%if %hijack_gcc
# create symlinks for lib64 / lib mappings (gcc!)
mkdir -p "%{buildroot}%{our_path}/usr/lib/"
# binutils secondary directories
mkdir -p %{buildroot}%{our_path}/usr/armv7el-tizen-linux-gnueabi/
ln -sf ../bin %{buildroot}%{our_path}/usr/armv7el-tizen-linux-gnueabi/bin

ln -sf ../lib64/gcc "%{buildroot}%{our_path}/usr/lib/gcc"
# g++ can also be called c++
ln -sf g++ "%{buildroot}%{our_path}/usr/bin/c++"
# gcc can also be called cc
ln -sf gcc "%{buildroot}%{our_path}/usr/bin/cc"
# gcc can also be called gcc-4.7
ln -sf gcc "%{buildroot}%{our_path}/usr/bin/gcc-4.7"

# nasty hack: If LIBRARY_PATH is set, native gcc adds the contents to its
#             library search list, but cross gcc does not. So switch to all
#             native in these situations.
mv %{buildroot}%{our_path}/usr/bin/gcc{,.real}
echo '#!/bin/bash
if [ "$LIBRARY_PATH" ]; then
  mv %{our_path}{,.bkp}
  exec /usr/bin/qemu-arm /usr/bin/gcc "$@"
fi
exec -a /usr/bin/gcc %{our_path}/usr/bin/gcc.real "$@"
' > %{buildroot}%{our_path}/usr/bin/gcc
chmod +x %{buildroot}%{our_path}/usr/bin/gcc
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
  exec /usr/bin/qemu-arm /usr/bin/ld "${args[@]}"
fi
for i in "$@"; do
  if [ "${i:0:10}" = "--sysroot=" ]; then
    exec -a "$0" %{our_path}/usr/arm-tizen-linux-gnueabi/bin/ld.real "$@"
  fi
done

exec -a "$0" %{our_path}/usr/arm-tizen-linux-gnueabi/bin/ld.real --sysroot=/ "$@"
' > %{buildroot}%{our_path}/usr/arm-tizen-linux-gnueabi/bin/ld
chmod +x %{buildroot}%{our_path}/usr/arm-tizen-linux-gnueabi/bin/ld

# To support gcc sysroot
mkdir -p %{buildroot}/usr/armv7el-tizen-linux-gnueabi
ln -sf .. %{buildroot}/usr/armv7el-tizen-linux-gnueabi/usr
%endif

# Make QEMU available through /qemu
mkdir %buildroot/qemu
cp -L /usr/bin/qemu-arm{,-binfmt} %buildroot/qemu/

%fdupes -s %{buildroot}

export NO_BRP_CHECK_RPATH="true"

# Install glibc-locale, otherwise msgmerge >= 0.18.3 fails
cp -R /usr/lib/{gconv,locale} %{buildroot}%{our_path}/usr/lib
cp -R /usr/share/locale %{buildroot}%{our_path}/usr/share
# Fix permissions for abuild
chmod 755 %{buildroot}%{our_path}/usr/lib/{gconv,locale}
chmod 755 %{buildroot}%{our_path}/usr/share/locale

%post
set -x
if [ $(uname -m) = armv7l ]; then
    # XXX find a way around this for cross-gcc
    mkdir -p /usr/lib64/gcc /lib64 || true
    ln -sf ../../lib/gcc/armv7el-tizen-linux-gnueabi /usr/lib64/gcc/armv7hl-tizen-linux-gnueabi || true
    ln -sf %{our_path}/lib64/libnsl.so.1 /lib64/libnsl.so.1 || true
fi
%if %use_icecream
chmod 4755 %{our_path}/usr/bin/schroot
%endif
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
rm -rf /usr/armv7el-tizen-linux-gnueabi/lib
ln -s /lib /usr/armv7el-tizen-linux-gnueabi/lib

%files
%defattr(-,root,root)  
%if %use_icecream
/etc/profile.d
/etc/pam.d
/etc/schroot
/lib64/security/pam_permit.so
/usr/share/icecream-envs
/opt/icecream/bin
%endif
%dir /usr/armv7el-tizen-linux-gnueabi
/usr/armv7el-tizen-linux-gnueabi/usr
/emul
/qemu
/usr/lib64

%changelog
