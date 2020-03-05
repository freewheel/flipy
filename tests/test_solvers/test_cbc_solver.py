import mock

import pytest

from flipy import CBCSolver


@pytest.fixture
def cbc_solver():
    return CBCSolver()


class TestCBCSolver:

    def test_init(self):
        solver = CBCSolver()
        assert solver.mip_gap == 0.1
        assert solver.timeout is None

    @mock.patch('platform.system')
    @mock.patch('platform.architecture')
    @pytest.mark.parametrize('system, arch, bin_path', [
        ('Linux', '64bit', 'cbc-linux64'),
        ('Linux', '64bit', 'bin/cbc-linux64/cbc'),
        ('Darwin', '64bit', 'bin/cbc-osx/cbc'),
        ('Windows', '32bit', 'bin/cbc-win32/cbc.exe'),
        ('Windows', '64bit', 'bin/cbc-win64/cbc.exe'),
    ])
    def test_find_binary(self, mock_arch, mock_system, system, arch, bin_path, cbc_solver):
        mock_arch.return_value = arch, None
        mock_system.return_value = system
        assert bin_path in cbc_solver._find_cbc_binary()

    @mock.patch('platform.system')
    @mock.patch('platform.architecture')
    def test_unknown_sys(self, mock_arch, mock_system, cbc_solver):
        mock_system.return_value = 'Plan9'
        mock_arch.return_value = '32bit', None
        with pytest.raises(Exception) as e:
            cbc_solver._find_cbc_binary()
        assert str(
            e.value
        ) == "no CBC solver found for system Plan9 32bit, please set the solver path manually with " \
             "environment variable 'CBC_SOLVER_BIN'"

    def test_find_custom_binary(self, monkeypatch, cbc_solver):
        monkeypatch.setenv('CBC_SOLVER_BIN', '/my_custom_cbc_binary')
        assert cbc_solver._find_cbc_binary() == '/my_custom_cbc_binary'

