%global		major			45

Summary:	JavaScript interpreter and libraries
Name:		mozjs%{major}
Version:	45.8.0
Release:	1%{?dist}
License:	MPLv2.0 and MPLv1.1 and BSD and GPLv2+ and GPLv3+ and LGPLv2.1 and LGPLv2.1+ and AFL and ASL 2.0
URL:		https://developer.mozilla.org/en-US/docs/Mozilla/Projects/SpiderMonkey/Releases/45
Source0:        https://ftp.mozilla.org/pub/firefox/releases/%{version}esr/source/firefox-%{version}esr.source.tar.xz
Source1:        LICENSE.txt

# According to mozilla devs x86_64 is the only 64-bit architecture. I tend to not agree with them.
Patch0:	fix-64bit-archs.patch
# same issue on s390 as in XUL/FF - https://bugzilla.redhat.com/show_bug.cgi?id=1219542
Patch1: rhbz-1219542-s390-build.patch
# Manually mmap on arm64 to ensure high 17 bits are clear
Patch2: mozbz-1143022+1277742.patch
# Fix AtomicOperations detection for disabled JIT
Patch3: fix-atomicoperatios.patch
# Make these functions visible in shared library (used by mongodb package):
# JS::UTF8CharsToNewTwoByteCharsZ
# JS::LossyUTF8CharsToNewTwoByteCharsZ
# js::DisableExtraThreads()
# js::ReportOutOfMemory()
Patch4: functions-visibility.patch

BuildRequires:	pkgconfig(icu-i18n)
BuildRequires:	pkgconfig(nspr)
BuildRequires:	pkgconfig(libffi)
BuildRequires:	pkgconfig(zlib)
BuildRequires:	readline-devel
BuildRequires:	/usr/bin/zip
BuildRequires:	python-devel
BuildRequires:	perl-devel

# Firefox does not allow to build with system version of jemalloc
Provides: bundled(jemalloc) = 4.0.0-12.ged4883285e111b426e5769b24dad164ebacaa5b9

%description
JavaScript is the Netscape-developed object scripting language used in millions
of web pages and server applications worldwide. Netscape's JavaScript is a
super set of the ECMA-262 Edition 3 (ECMAScript) standard scripting language,
with only mild differences from the published standard.

%package devel
Summary: Header files, libraries and development documentation for %{name}
Group: Development/Libraries
Requires: %{name}%{?_isa} = %{version}-%{release}

%description devel
This package contains the header files, static libraries and development
documentation for %{name}. If you like to develop programs using %{name},
you will need to install %{name}-devel.

%prep
%setup -q -n firefox-%{version}esr/js/src
%patch0 -p1
%ifarch s390
%patch1 -p3 -b .rhbz-1219542-s390
%endif
%patch2 -p3
%patch3 -p1
pushd ../..
%patch4 -p1
popd

%if 0%{?fedora} > 22
# Correct failed to link tests due to hardened build
sed -i 's|"-O2"|"-O2 -fPIC"|' configure
%endif

# Remove zlib directory (to be sure using system version)
rm -rf ../../modules/zlib

# Fix release number
head -n -1 ../../config/milestone.txt > ../../config/milestone.txt
echo "%{version}" >> ../../config/milestone.txt

%build
# Disable null pointer gcc6 optimization in gcc6 (rhbz#1328045)
export CFLAGS="%{optflags} -fno-tree-vrp -fno-strict-aliasing -fno-delete-null-pointer-checks"
export CXXFLAGS=$CFLAGS
LINKFLAGS="%{?__global_ldflags}"
export PYTHON=/usr/bin/python2

%configure \
 --enable-optimize \
 --enable-pie \
 --enable-posix-nspr-emulation \
 --enable-readline \
 --enable-release \
 --enable-shared-js \
 --enable-system-ffi \
 --enable-xterm-updates \
 --with-pthreads \
 --with-system-icu \
 --with-system-zlib \
 --with-intl-api \
%ifarch %{arm} aarch64 ppc ppc64 ppc64le
 --disable-ion
%endif

# Without adding these sources resulted library has weak symbols
echo "CPPSRCS += \$(DEPTH)/mfbt/Unified_cpp_mfbt0.cpp \$(DEPTH)/../../mfbt/Compression.cpp \$(DEPTH)/../../mfbt/decimal/Decimal.cpp" >> js/src/backend.mk
#echo "STATIC_LIBS += \$(DEPTH)/mfbt/libmfbt.a" >> js/src/backend.mk

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

mv %{buildroot}%{_libdir}/pkgconfig/js.pc %{buildroot}%{_libdir}/pkgconfig/mozjs-%{major}.pc
chmod a-x  %{buildroot}%{_libdir}/pkgconfig/*.pc

# Do not install binaries or static libraries
rm -f %{buildroot}%{_libdir}/*.a %{buildroot}%{_libdir}/*.ajs %{buildroot}%{_bindir}/js*

# Install files, not symlinks to build directory
pushd %{buildroot}%{_includedir}
    for link in `find . -type l`; do
	header=`readlink $link`
	rm -f $link
	cp -p $header $link
    done
popd
cp -p js/src/js-config.h %{buildroot}%{_includedir}/mozjs-%{major}

# Install license file
cp %{SOURCE1} .

%check
# Run SpiderMonkey tests
tests/jstests.py -d -s -t 1800 --no-progress ../../js/src/js/src/shell/js

# Run basic JIT tests
jit-test/jit_test.py -s -t 1800 --no-progress ../../js/src/js/src/shell/js basic

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%license LICENSE.txt
%doc ../../README.txt
%{_libdir}/*.so

%files devel
%{_libdir}/pkgconfig/*.pc
%{_includedir}/mozjs-%{major}

%changelog
* Tue Mar 07 2017 Fedora Release Monitoring  <release-monitoring@fedoraproject.org> - 45.8.0-1
- Update to 45.8.0 (#1429732)

* Tue Feb 21 2017 Marek Skalický <mskalick@redhat.com> - 45.7.0-3
- Enable Internationalization api
- Make more functions visible in shared library

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 45.7.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Feb 03 2017 Marek Skalický <mskalick@redhat.com> - 45.7.0-1
- Update to latest minor release

* Fri Dec 16 2016 Marek Skalický <mskalick@redhat.com> - 45.6.0-1
- Update to latest minor release

* Thu Dec 08 2016 Marek Skalický <mskalick@redhat.com> - 45.5.1-2
- Allow using gcc buildin AtomicOperations also for s390x and MIPS

* Mon Dec 05 2016 Marek Skalický <mskalick@redhat.com> - 45.5.1-1
- Update to latest minor version 45.5.1

* Mon Nov 21 2016 Marek Skalický <mskalick@redhat.com> - 45.5.0-2
- Disable ION (JIT) for ARM and PPC architectures
- Fixed producing weak symbols in libmozjs-45.so
- Make tests passing on all architectures
- Fixed platform detection of AtomicOperations with disabled ION
- Update to 45.5.0

* Thu Oct 06 2016 Marek Skalický <mskalick@redhat.com> - 45.4.0-1
- Update to latest ESR release 45.4.0

* Fri Sep 16 2016 Marek Skalický <mskalick@redhat.com> - 45.3.0-1
- Update to latest ESR release

* Tue Jul  5 2016 Peter Robinson <pbrobinson@fedoraproject.org> 45.1.1-6
- Add upstream patches for aarch64 48-bit VA

* Mon May 30 2016 Marek Skalický <mskalick@redhat.com> - 45.1.1-5
- Disable tests for arm

* Mon May 30 2016 Dan Horák <dan[at]danny.cz> - 45.1.1-4
- Fix build on s390 by refreshing the build patch

* Tue May 24 2016 Marek Skalicky <mskalick@redhat.com> - 45.1.1-3
- Fixed license handling

* Mon May 23 2016 Marek Skalicky <mskalick@redhat.com> - 45.1.1-2
- Fixed some errors from package review

* Tue May 17 2016 Marek Skalicky <mskalick@redhat.com> - 45.1.1-1
- Initial packaging of mozjs 45
