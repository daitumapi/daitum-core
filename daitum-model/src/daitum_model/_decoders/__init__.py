# Copyright 2026 Daitum
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

"""
Model decoder subpackage.

Call :func:`register_all` to register every model decoder on the shared registries in
:mod:`daitum_model.decoding`. ``daitum_model.__init__`` calls it once on import so the
decoders are available whenever the package is used.
"""

from daitum_model._decoders import fields, formula, named_values, tables
from daitum_model._decoders.model import decode_model
from daitum_model.decoding import register_decoder
from daitum_model.model import ModelBuilder

_done: set[str] = set()


def register_all() -> None:
    """Register every model decoder. Idempotent — safe to call more than once."""
    if _done:
        return
    formula.register()
    fields.register()
    named_values.register()
    tables.register()
    # Register the top-level builder so decode_into(ModelBuilder, ...) dispatches here too,
    # mirroring ConfigurationBuilder/UiBuilder.
    register_decoder(ModelBuilder, decode_model)
    _done.add("registered")


__all__ = ["decode_model", "register_all"]
