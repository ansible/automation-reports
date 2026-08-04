from unittest.mock import patch, mock_open

import pytest

from backend.apps.dispatch.pool import _get_mem_in_bytes, _get_cpu_count, get_auto_max_workers


class TestGetMemInBytes:

    def test_env_var_override_takes_priority(self):
        with patch.dict('os.environ', {'SYSTEM_TASK_ABS_MEM': '4294967296'}):
            assert _get_mem_in_bytes() == 4294967296

    def test_env_var_override_invalid_falls_through_to_procmeminfo(self):
        def fake_open(path, *args, **kwargs):
            if 'cgroup' in path:
                raise FileNotFoundError
            return mock_open(read_data='MemTotal: 8192000 kB\n')()

        with patch.dict('os.environ', {'SYSTEM_TASK_ABS_MEM': 'notanumber'}):
            with patch('builtins.open', side_effect=fake_open):
                assert _get_mem_in_bytes() == 8192000 * 1024

    def test_cgroup_v2_limit_used_when_not_max(self):
        def fake_open(path, *args, **kwargs):
            if 'memory.max' in path:
                return mock_open(read_data='4294967296\n')()
            raise FileNotFoundError

        with patch.dict('os.environ', {}, clear=False):
            with patch('builtins.open', side_effect=fake_open):
                assert _get_mem_in_bytes() == 4294967296

    def test_cgroup_v2_max_skips_to_proc_meminfo(self):
        def fake_open(path, *args, **kwargs):
            if 'memory.max' in path:
                return mock_open(read_data='max\n')()
            return mock_open(read_data='MemTotal: 4096000 kB\n')()

        with patch('builtins.open', side_effect=fake_open):
            assert _get_mem_in_bytes() == 4096000 * 1024

    def test_proc_meminfo_read(self):
        def fake_open(path, *args, **kwargs):
            if 'cgroup' in path:
                raise FileNotFoundError
            return mock_open(read_data='MemTotal: 16384000 kB\nMemFree: 8192000 kB\n')()

        with patch('builtins.open', side_effect=fake_open):
            assert _get_mem_in_bytes() == 16384000 * 1024

    def test_oserror_on_proc_meminfo_returns_fallback(self):
        with patch('builtins.open', side_effect=PermissionError):
            assert _get_mem_in_bytes() == 2 * 1024 * 1024 * 1024

    def test_file_not_found_returns_fallback(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            assert _get_mem_in_bytes() == 2 * 1024 * 1024 * 1024

    def test_malformed_proc_meminfo_returns_fallback(self):
        def fake_open(path, *args, **kwargs):
            if 'cgroup' in path:
                raise FileNotFoundError
            return mock_open(read_data='MemTotal: not_a_number kB\n')()

        with patch('builtins.open', side_effect=fake_open):
            assert _get_mem_in_bytes() == 2 * 1024 * 1024 * 1024


class TestGetCpuCount:

    def test_env_var_override(self):
        with patch.dict('os.environ', {'SYSTEM_TASK_ABS_CPU': '8'}):
            assert _get_cpu_count() == 8

    def test_env_var_invalid_falls_through(self):
        def fake_open(path, *args, **kwargs):
            raise FileNotFoundError

        with patch.dict('os.environ', {'SYSTEM_TASK_ABS_CPU': 'notanumber'}):
            with patch('builtins.open', side_effect=fake_open):
                with patch('multiprocessing.cpu_count', return_value=4):
                    assert _get_cpu_count() == 4

    def test_cgroup_v2_quota(self):
        def fake_open(path, *args, **kwargs):
            if 'cpu.max' in path:
                return mock_open(read_data='200000 100000\n')()
            raise FileNotFoundError

        with patch('builtins.open', side_effect=fake_open):
            assert _get_cpu_count() == 2

    def test_cgroup_v2_quota_rounds_down_to_one_minimum(self):
        def fake_open(path, *args, **kwargs):
            if 'cpu.max' in path:
                return mock_open(read_data='50000 100000\n')()
            raise FileNotFoundError

        with patch('builtins.open', side_effect=fake_open):
            assert _get_cpu_count() == 1

    def test_cgroup_v2_max_skips_to_cpu_count(self):
        def fake_open(path, *args, **kwargs):
            if 'cpu.max' in path:
                return mock_open(read_data='max 100000\n')()
            raise FileNotFoundError

        with patch('builtins.open', side_effect=fake_open):
            with patch('multiprocessing.cpu_count', return_value=6):
                assert _get_cpu_count() == 6

    def test_oserror_falls_back_to_cpu_count(self):
        with patch('builtins.open', side_effect=PermissionError):
            with patch('multiprocessing.cpu_count', return_value=4):
                assert _get_cpu_count() == 4

    def test_file_not_found_falls_back_to_cpu_count(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('multiprocessing.cpu_count', return_value=2):
                assert _get_cpu_count() == 2


class TestGetAutoMaxWorkers:

    def test_memory_bound_returns_mem_capacity(self):
        with patch('backend.apps.dispatch.pool._get_mem_in_bytes', return_value=16 * 1024 ** 3), \
             patch('backend.apps.dispatch.pool._get_cpu_count', return_value=4), \
             patch('backend.apps.dispatch.pool.get_corrected_memory', return_value=16 * 1024 ** 3), \
             patch('backend.apps.dispatch.pool.get_mem_effective_capacity', return_value=20), \
             patch('backend.apps.dispatch.pool.get_corrected_cpu', return_value=4), \
             patch('backend.apps.dispatch.pool.get_cpu_effective_capacity', return_value=8):
            assert get_auto_max_workers() == 20

    def test_cpu_bound_returns_cpu_capacity(self):
        with patch('backend.apps.dispatch.pool._get_mem_in_bytes', return_value=2 * 1024 ** 3), \
             patch('backend.apps.dispatch.pool._get_cpu_count', return_value=32), \
             patch('backend.apps.dispatch.pool.get_corrected_memory', return_value=2 * 1024 ** 3), \
             patch('backend.apps.dispatch.pool.get_mem_effective_capacity', return_value=4), \
             patch('backend.apps.dispatch.pool.get_corrected_cpu', return_value=32), \
             patch('backend.apps.dispatch.pool.get_cpu_effective_capacity', return_value=48):
            assert get_auto_max_workers() == 48

    def test_equal_capacities_returns_either(self):
        with patch('backend.apps.dispatch.pool._get_mem_in_bytes', return_value=8 * 1024 ** 3), \
             patch('backend.apps.dispatch.pool._get_cpu_count', return_value=8), \
             patch('backend.apps.dispatch.pool.get_corrected_memory', return_value=8 * 1024 ** 3), \
             patch('backend.apps.dispatch.pool.get_mem_effective_capacity', return_value=10), \
             patch('backend.apps.dispatch.pool.get_corrected_cpu', return_value=8), \
             patch('backend.apps.dispatch.pool.get_cpu_effective_capacity', return_value=10):
            assert get_auto_max_workers() == 10
