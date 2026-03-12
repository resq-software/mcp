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

FROM python:3.13-alpine3.21 AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

# Install build dependencies
RUN pip install build
# Build wheel
RUN python -m build

FROM python:3.13-alpine3.21

WORKDIR /app

# Create non-root user
RUN adduser -D -u 1000 resq
USER resq

COPY --from=builder /app/dist/*.whl /app/
RUN pip install --no-cache-dir /app/*.whl

# Copy config and source (for any direct usage if needed, though wheel installed it)
# We might running via `python -m resq_mcp.server`

# Expose port for SSE
EXPOSE 8000

ENV RESQ_HOST=0.0.0.0
ENV RESQ_PORT=8000

# Default entrypoint for SSE mode
# Ensure we use the proper FastMCP command syntax or our own wrapper
# FastMCP typically exposes a CLI.
# "fastmcp run resq_mcp.server:mcp" is common, or if we use our own __main__ block:
CMD ["python", "-m", "resq_mcp.server"]