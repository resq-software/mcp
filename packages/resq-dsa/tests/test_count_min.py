# Copyright 2026 ResQ Software
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

from resq_dsa.count_min import CountMinSketch


def test_frequency():
    cms = CountMinSketch(0.01, 0.01)
    cms.increment("a", 5)
    cms.increment("a", 3)
    cms.increment("b", 1)
    assert cms.estimate("a") >= 8 and cms.estimate("b") >= 1
    assert cms.estimate("ghost") == 0
