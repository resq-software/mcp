# Copyright 2026 ResQ
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for centralized timeout configuration."""

from __future__ import annotations

import os
from unittest.mock import patch


class TestTimeoutConfig:
    def test_default_request_timeout(self) -> None:
        from resq_mcp.core.timeout import get_default_timeout

        timeout = get_default_timeout()
        assert timeout.total == 30.0
        assert timeout.connect == 5.0

    def test_env_var_override(self) -> None:
        from resq_mcp.core.timeout import get_default_timeout

        with patch.dict(os.environ, {"RESQ_REQUEST_TIMEOUT": "60.0"}):
            timeout = get_default_timeout()
            assert timeout.total == 60.0

    def test_polling_interval_exponential_backoff(self) -> None:
        from resq_mcp.core.timeout import get_polling_interval

        intervals = [get_polling_interval(i) for i in range(5)]
        assert intervals[0] == 1.0
        assert intervals[1] == 2.0
        assert intervals[2] == 4.0
        assert intervals[3] == 5.0
        assert intervals[4] == 5.0

    def test_max_polling_attempts_default(self) -> None:
        from resq_mcp.core.timeout import get_max_polling_attempts

        assert get_max_polling_attempts() == 30
