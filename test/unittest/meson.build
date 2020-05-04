unittest_nntrainer_internal_deps = [
  nntrainer_unittest_deps,
  gtest_dep
]

unittest_nntrainer_src=[
  'unittest_nntrainer_internal.cpp',
  '../nntrainer_test_util.cpp'
]


unzip_target = ['trainset.tar.gz', 'valset.tar.gz', 'testset.tar.gz']
src_path = join_paths(meson.source_root(), 'packaging')
dest_path = meson.build_root()

foreach target: unzip_target
  _src_path = join_paths(src_path, target)
  run_command(['tar', 'xzf', _src_path, '-C', dest_path])
endforeach

run_command(['cp', join_paths(src_path, 'label.dat'), join_paths(dest_path, 'label.dat')])

unittest_nntrainer_internal = executable('unittest_nntrainer_internal',
  unittest_nntrainer_src,
  dependencies: [unittest_nntrainer_internal_deps],
  include_directories: nntrainer_test_inc,
  install: get_option('enable-test'),
  install_dir: application_install_dir
)
test('unittest_nntrainer_internal', unittest_nntrainer_internal)


unittest_util_func = executable('unittest_util_func',
  'unittest_util_func.cpp',
  dependencies: [unittest_nntrainer_internal_deps],
  install: get_option('enable-test'),
  install_dir: application_install_dir
)
test('unittest_util_func', unittest_util_func)