# Execute gbs with --define "testcoverage 1" in case that you must get unittest coverage statistics
%define         use_cblas 1
%define         nnstreamer_filter 1
%define         use_gym 0
%define         support_ccapi 1
%define         support_nnstreamer_backbone 1
%define         support_tflite_backbone 1
%define         support_tflite_interpreter 1
%define         nntrainerapplicationdir %{_libdir}/nntrainer/bin
%define         gen_input $(pwd)/test/input_gen/genInput.py
%define         support_data_augmentation_opencv 1

%bcond_with tizen

# dependency resolution
%if 0%{tizen_version_major}%{tizen_version_minor} >= 65
# (rpm -qi nnstreamer --queryformat '%%{VERSION}' | sed -e 's/\.//g') >= 171

%define         capi_machine_learning_common	   capi-machine-learning-common
%define         capi_machine_learning_inference	 capi-machine-learning-inference

%define         capi_ml_common_pkg_name          capi-ml-common
%define         capi_ml_inference_pkg_name       capi-ml-inference

%else

%if 0%{tizen_version_major}%{tizen_version_minor} >= 60
# (rpm -qi nnstreamer --queryformat '%%{VERSION}' | sed -e 's/\.//g') >= 160
%define         capi_machine_learning_common     capi-ml-common
%define         capi_machine_learning_inference  capi-nnstreamer

%define         capi_ml_common_pkg_name          capi-nnstreamer
%define         capi_ml_inference_pkg_name       capi-nnstreamer
%else
%{error: nnst_version < 6.0 is not supported}
# shouldn't reach here. Below is for the reference.
# If you prepare ml-common-api.h, below can work though.
%define         capi_machine_learning_inference  capi-nnstreamer
%define         capi_machine_learning_common	   capi-nnstreamer

%define         capi_ml_common_pkg_name          capi-nnstreamer
%define         capi_ml_inference_pkg_name       capi-nnstreamer
%endif # 0%{tizen_version_major}%{tizen_version_minor} >= 60

%endif # 0%{tizen_version_major}%{tizen_version_minor} >= 65

Name:		nntrainer
Summary:	Software framework for training neural networks
Version:	0.2.0
Release:	0
Packager:	Jijoong Moon <jijoong.moon@samsung.com>
License:	Apache-2.0
Source0:	nntrainer-%{version}.tar.gz
Source1001:	nntrainer.manifest
%if %{with tizen}
Source1002:     capi-machine-learning-training.manifest
%endif
Source2001:	trainset.tar.gz
Source2002:	valset.tar.gz
Source2003:	testset.tar.gz
Source2004:	label.dat
Source2005:	unittest_layers.tar.gz

BuildRequires:	meson >= 0.50.0
BuildRequires:	openblas-devel
BuildRequires:	iniparser-devel >= 4.1
BuildRequires:	gtest-devel
BuildRequires:	python3
BuildRequires:	python3-numpy

BuildRequires:	%{capi_machine_learning_common}-devel

%if 0%{?unit_test}
BuildRequires:	ssat >= 1.1.0
%endif

# OpenAI interface
%define enable_gym -Duse_gym=false
%if 0%{?use_gym}
BuildRequires:	gym-http-api-devel
%define enable_gym -Duse_gym=true
%endif

%if 0%{?testcoverage}
# to be compatible with gcc-9, lcov should have a higher version than 1.14.1
BuildRequires: lcov
# BuildRequires:	taos-ci-unittest-coverage-assessment
%endif

%if 0%{?support_data_augmentation_opencv}
BuildRequires: opencv-devel
%endif

%if %{with tizen}
BuildRequires:	pkgconfig(capi-system-info)
BuildRequires:	pkgconfig(capi-base-common)
BuildRequires:	pkgconfig(dlog)

%if 0%{?support_nnstreamer_backbone}
BuildRequires: nnstreamer-tensorflow2-lite
BuildRequires: %{capi_machine_learning_inference}-devel

Requires:	nnstreamer-tensorflow2-lite
Requires:	%{capi_machine_learning_inference}
%endif # support_nnstreamer_backbone

%if 0%{?support_tflite_backbone}
BuildRequires: tensorflow2-lite-devel
%endif # support_tflite_backbone

%if 0%{?support_tflite_interpreter}
BuildRequires: tensorflow2-lite-devel
%endif # support_tflite_interpreter

%define enable_nnstreamer_tensor_filter -Denable-nnstreamer-tensor-filter=false

%if  0%{?nnstreamer_filter}
BuildRequires:	nnstreamer-devel
%define enable_nnstreamer_tensor_filter -Denable-nnstreamer-tensor-filter=true

%if 0%{?unit_test}
BuildRequires:	nnstreamer-test-devel
BuildRequires:	gst-plugins-good-extra
BuildRequires:	python
%endif #unit_test
%endif #nnstreamer_filter
%endif  # tizen

Requires:	nntrainer-core = %{version}-%{release}

%if 0%{?nnstreamer_filter}
Requires:	nnstreamer-nntrainer = %{version}-%{release}
%endif #nnstreamer_filter
%if %{with tizen}
Requires:	capi-machine-learning-training = %{version}-%{release}
%endif #tizen

%description
NNtrainer Meta package for tizen

%package core
Summary:	Software framework for training neural networks
Requires:	iniparser >= 4.1
Requires:	libopenblas_pthreads0

%description core
NNtrainer is Software Framework for Training Neural Network Models on Devices.

%package devel
Summary:	Development package for custom nntrainer developers
Requires:	nntrainer = %{version}-%{release}
Requires:	openblas-devel
Requires:	%{capi_machine_learning_common}-devel

%description devel
Development package for custom nntrainer developers.
This contains corresponding header files and .pc pkgconfig file.

%package devel-static
Summary:        Static library for nntrainer-devel package
Requires:       devel = %{version}-%{release}
%description devel-static
Static library package of nntrainer-devel

%package applications
Summary:	NNTrainer Examples
Requires:	nntrainer = %{version}-%{release}
Requires:	%{capi_machine_learning_inference}
Requires:	nnstreamer-tensorflow2-lite
BuildRequires:  nnstreamer-test-devel
BuildRequires:	nnstreamer-tensorflow2-lite
BuildRequires:	tensorflow2-lite-devel
BuildRequires:	pkgconfig(jsoncpp)
BuildRequires:	pkgconfig(libcurl)
BuildRequires:	pkgconfig(dlog)
BuildRequires:	%{capi_machine_learning_inference}-devel
BuildRequires:	glib2-devel
BuildRequires:  gstreamer-devel

%description applications
NNTrainer Examples for test purpose.

%if 0%{?testcoverage}
%package unittest-coverage
Summary:	NNTrainer UnitTest Coverage Analysis Result

%description unittest-coverage
HTML pages of lcov results of NNTrainer generated during rpmbuild
%endif

%if %{with tizen}
%package -n capi-machine-learning-training
Summary:         Tizen Native API for NNTrainer
Group:           Multimedia/Framework
Requires:        %{name} = %{version}-%{release}
%description -n capi-machine-learning-training
Tizen Native API wrapper for NNTrainer.
You can train neural networks efficiently.

%post -n capi-machine-learning-training -p /sbin/ldconfig
%postun -n capi-machine-learning-training -p /sbin/ldconfig

%package -n capi-machine-learning-training-devel
Summary:         Tizen Native API Devel Kit for NNTrainer
Group:           Multimedia/Framework
Requires:        capi-machine-learning-training = %{version}-%{release}
Requires:        %{capi_machine_learning_common}-devel
%description -n capi-machine-learning-training-devel
Developmental kit for Tizen Native NNTrainer API.

%package -n capi-machine-learning-training-devel-static
Summary:         Static library for Tizen Native API
Group:           Multimedia/Framework
Requires:        capi-machine-learning-training-devel = %{version}-%{release}
%description -n capi-machine-learning-training-devel-static
Static library of capi-machine-learning-training-devel package.

%if 0%{?support_ccapi}
%package -n ccapi-machine-learning-training
Summary:         Tizen Native API for NNTrainer
Group:           Multimedia/Framework
Requires:        %{name} = %{version}-%{release}
%description -n ccapi-machine-learning-training
Tizen Native API wrapper for NNTrainer.
You can train neural networks efficiently.

%post -n ccapi-machine-learning-training -p /sbin/ldconfig
%postun -n ccapi-machine-learning-training -p /sbin/ldconfig

%package -n ccapi-machine-learning-training-devel
Summary:         Tizen Native API Devel Kit for NNTrainer
Group:           Multimedia/Framework
Requires:        ccapi-machine-learning-training = %{version}-%{release}
%description -n ccapi-machine-learning-training-devel
Developmental kit for Tizen Native NNTrainer API.

%package -n ccapi-machine-learning-training-devel-static
Summary:         Static library for Tizen c++ API
Group:           Multimedia/Framework
Requires:        ccapi-machine-learning-training-devel = %{version}-%{release}
%description -n ccapi-machine-learning-training-devel-static
Static library of ccapi-machine-learning-training-devel package.
%endif

%if 0%{?nnstreamer_filter}
%package -n nnstreamer-nntrainer
Summary: NNStreamer NNTrainer support
Requires: %{name} = %{version}-%{release}
Requires:	nnstreamer
%description -n nnstreamer-nntrainer
NNSteamer tensor filter for nntrainer to support inference.

%package -n nnstreamer-nntrainer-devel-static
Summary: NNStreamer NNTrainer support
Requires: devel-static = %{version}-%{release}
Requires:	nnstreamer-nntrainer
%description -n nnstreamer-nntrainer-devel-static
NNSteamer tensor filter static package for nntrainer to support inference.
%endif #nnstreamer_filter

%endif #tizen

## Define build options
%define enable_tizen -Denable-tizen=false
%define enable_tizen_feature_check -Denable-tizen-feature-check=true
%define install_app -Dinstall-app=true
%define enable_ccapi -Denable-ccapi=false
%define enable_nnstreamer_backbone -Denable-nnstreamer-backbone=false
%define enable_tflite_backbone -Denable-tflite-backbone=false
%define enable_tflite_interpreter -Denable-tflite-interpreter=false
%define enable_profile -Denable-profile=false
%define capi_ml_pkg_dep_resolution -Dcapi-ml-inference-actual=%{?capi_ml_inference_pkg_name} -Dcapi-ml-common-actual=%{?capi_ml_common_pkg_name}
%define enable_reduce_tolerance -Dreduce-tolerance=true

# enable full tolerance on the CI
%if 0%{?unit_test}
%define enable_reduce_tolerance -Dreduce-tolerance=false
%endif

%if %{with tizen}
%define enable_tizen -Denable-tizen=true

%if 0%{?support_ccapi}
%define enable_ccapi -Denable-ccapi=true
%endif # support_ccapi
%endif # tizen

# Using cblas for Matrix calculation
%if 0%{?use_cblas}
%define enable_cblas -Denable-blas=true
%endif

%if 0%{?support_nnstreamer_backbone}
%define enable_nnstreamer_backbone -Denable-nnstreamer-backbone=true
%endif

%if 0%{?support_tflite_backbone}
%define enable_tflite_backbone -Denable-tflite-backbone=true
%endif

%if 0%{?unit_test}
%define enable_profile -Denable-profile=true
%endif

%if 0%{?support_tflite_interpreter}
%define enable_tflite_interpreter -Denable-tflite-interpreter=true
%endif

%prep
%setup -q
cp %{SOURCE1001} .
cp %{SOURCE2001} .
cp %{SOURCE2002} .
cp %{SOURCE2003} .
cp %{SOURCE2004} .
cp %{SOURCE2005} .

%if %{with tizen}
cp %{SOURCE1002} .
%endif

%build
CXXFLAGS=`echo $CXXFLAGS | sed -e "s|-std=gnu++11||"`

%if 0%{?testcoverage}
CXXFLAGS="${CXXFLAGS} -fprofile-arcs -ftest-coverage"
CFLAGS="${CFLAGS} -fprofile-arcs -ftest-coverage"
%endif

# Add backward competibility for tizen < 6
%if 0%{tizen_version_major} < 6
ln -sf %{_includedir}/nnstreamer/nnstreamer.h %{_includedir}/nnstreamer/ml-api-common.h
ln -sf %{_libdir}/pkgconfig/capi-nnstreamer.pc %{_libdir}/pkgconfig/capi-ml-common.pc
%endif

mkdir -p build
meson --buildtype=plain --prefix=%{_prefix} --sysconfdir=%{_sysconfdir} \
      --libdir=%{_libdir} --bindir=%{nntrainerapplicationdir} \
      --includedir=%{_includedir} %{install_app} %{enable_tizen} \
      %{enable_tizen_feature_check} %{enable_cblas} %{enable_ccapi} \
      %{enable_gym} %{enable_nnstreamer_tensor_filter} %{enable_profile} \
      %{enable_nnstreamer_backbone} %{enable_tflite_backbone} \
      %{enable_tflite_interpreter} %{capi_ml_pkg_dep_resolution} \
      %{enable_reduce_tolerance} build

ninja -C build %{?_smp_mflags}

%if 0%{?unit_test}
export NNSTREAMER_CONF=$(pwd)/test/nnstreamer/nnstreamer-test.ini
export NNSTREAMER_FILTERS=$(pwd)/build/nnstreamer/tensor_filter
meson test -C build -t 2.0 --print-errorlogs

# unittest for nntrainer plugin for nnstreamer
# todo: migrate this to meson test soon
%if 0%{?nnstreamer_filter}
pushd test/nnstreamer
ssat
popd
%endif #nnstreamer_filter
%endif #unit_test

%install
DESTDIR=%{buildroot} ninja -C build %{?_smp_mflags} install

%if 0%{?testcoverage}
##
# The included directories are:
#
# api: nnstreamer api
# gst: the nnstreamer elements
# nnstreamer_example: custom plugin examples
# common: common libraries for gst (elements)
# include: common library headers and headers for external code (packaged as "devel")
#
# Intentionally excluded directories are:
#
# tests: We are not going to show testcoverage of the test code itself or example applications

%if %{with tizen}
%define testtarget $(pwd)/api/capi
%else
%define testtarget
%endif

# 'lcov' generates the date format with UTC time zone by default. Let's replace UTC with KST.
# If you ccan get a root privilege, run ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
TZ='Asia/Seoul'; export TZ
$(pwd)/test/unittestcoverage.py module $(pwd)/nntrainer %testtarget

# Get commit info
VCS=`cat ${RPM_SOURCE_DIR}/nntrainer.spec | grep "^VCS:" | sed "s|VCS:\\W*\\(.*\\)|\\1|"`

# Create human readable unit test coverage report web page.
# Create null gcda files if gcov didn't create it because there is completely no unit test for them.
find . -name "*.gcno" -exec sh -c 'touch -a "${1%.gcno}.gcda"' _ {} \;
# Remove gcda for meaningless file (CMake's autogenerated)
find . -name "CMakeCCompilerId*.gcda" -delete
find . -name "CMakeCXXCompilerId*.gcda" -delete
#find . -path "/build/*.j

# Generate report
lcov -t 'NNTrainer Unit Test Coverage' -o unittest.info -c -d . -b %{_builddir}/%{name}-%{version}/build --include "*/nntrainer/*" --include "*/api/*" --exclude "*/tensorflow/*" --exclude "*/nntrainer_logger.cpp"

# Exclude generated files
lcov -r unittest.info "*/test/*" "*/meson*/*" -o unittest-filtered.info

# Visualize the report
genhtml -o result unittest-filtered.info -t "nntrainer %{version}-%{release} ${VCS}" --ignore-errors source -p ${RPM_BUILD_DIR}

mkdir -p %{buildroot}%{_datadir}/nntrainer/unittest/
cp -r result %{buildroot}%{_datadir}/nntrainer/unittest/
%endif  # test coverage

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files

%files core
%manifest nntrainer.manifest
%defattr(-,root,root,-)
%license LICENSE
%{_libdir}/libnntrainer.so
%config %{_sysconfdir}/nntrainer.ini

%files devel
%{_includedir}/nntrainer/app_context.h
%{_includedir}/nntrainer/nntrainer_error.h
%{_includedir}/nntrainer/nntrainer_log.h
%{_includedir}/nntrainer/nntrainer_logger.h
%{_includedir}/nntrainer/acti_func.h
%{_includedir}/nntrainer/common_properties.h
%{_includedir}/nntrainer/loss_layer.h
%{_includedir}/nntrainer/weight.h
%{_includedir}/nntrainer/var_grad.h
%{_includedir}/nntrainer/base_properties.h
%{_includedir}/nntrainer/node_exporter.h
%{_includedir}/nntrainer/parse_util.h
%{_includedir}/nntrainer/graph_core.h
%{_includedir}/nntrainer/graph_node.h
%{_includedir}/nntrainer/databuffer.h
%{_includedir}/nntrainer/databuffer_factory.h
%{_includedir}/nntrainer/layer_internal.h
%{_includedir}/nntrainer/layer_factory.h
%{_includedir}/nntrainer/neuralnet.h
%{_includedir}/nntrainer/tensor.h
%{_includedir}/nntrainer/tensor_dim.h
%{_includedir}/nntrainer/optimizer_devel.h
%{_includedir}/nntrainer/optimizer_impl.h
%{_includedir}/nntrainer/optimizer_factory.h
%{_includedir}/nntrainer/profiler.h
%{_includedir}/nntrainer/dynamic_training_optimization.h
%{_includedir}/nntrainer/layer_node.h
%{_includedir}/nntrainer/manager.h
%{_includedir}/nntrainer/network_graph.h
%{_libdir}/pkgconfig/nntrainer.pc

%files devel-static
%{_libdir}/libnntrainer*.a
%exclude %{_libdir}/libcapi*.a

%if %{with tizen}
%files -n capi-machine-learning-training
%manifest capi-machine-learning-training.manifest
%license LICENSE
%{_libdir}/libcapi-nntrainer.so

%files -n capi-machine-learning-training-devel
%{_includedir}/nntrainer/nntrainer.h
%{_includedir}/nntrainer/nntrainer-api-common.h
%{_libdir}/pkgconfig/capi-ml-training.pc

%files -n capi-machine-learning-training-devel-static
%{_libdir}/libcapi-nntrainer.a

%if 0%{?support_ccapi}
%files -n ccapi-machine-learning-training
%manifest capi-machine-learning-training.manifest
%license LICENSE
%{_libdir}/libccapi-nntrainer.so

%files -n ccapi-machine-learning-training-devel
%{_includedir}/nntrainer/model.h
%{_includedir}/nntrainer/layer.h
%{_includedir}/nntrainer/optimizer.h
%{_includedir}/nntrainer/dataset.h
%{_libdir}/pkgconfig/ccapi-ml-training.pc

%files -n ccapi-machine-learning-training-devel-static
%{_libdir}/libccapi-nntrainer.a
%endif # support_ccapi

%if 0%{?nnstreamer_filter}
%files -n nnstreamer-nntrainer
%manifest nntrainer.manifest
%defattr(-,root,root,-)
%license LICENSE
%{_libdir}/nnstreamer/filters/libnnstreamer_filter_nntrainer.so

%files -n nnstreamer-nntrainer-devel-static
%manifest nntrainer.manifest
%defattr(-,root,root,-)
%license LICENSE
%{_libdir}/libnnstreamer_filter_nntrainer.a

%endif #nnstreamer_filter
%endif #tizen

%files applications
%manifest nntrainer.manifest
%defattr(-,root,root,-)
%license LICENSE
%{_libdir}/nntrainer/bin/applications/*

%if 0%{?testcoverage}
%files unittest-coverage
%{_datadir}/nntrainer/unittest/*
%endif

%changelog
* Wed Jun 02 2021 Jijoong Moon <jijoong.moon@samsung.com>
- Release of 0.2.0
* Wed Sep 23 2020 Jijoong Moon <jijoong.moon@samsung.com>
- Release of 0.1.1
* Mon Aug 10 2020 Jijoong Moon <jijoong.moon@samsung.com>
- Release of 0.1.0.rc1
* Wed Mar 18 2020 Jijoong Moon <jijoong.moon@samsung.com>
- packaged nntrainer
