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
UI decoder subpackage.

Call :func:`register_all` to register every UI decoder on the shared registries in
:mod:`daitum_model.decoding`. ``daitum_ui.__init__`` calls it once on import.
"""

from daitum_model.decoding import register_decoder

from daitum_ui._decoders import leaves, sections, views
from daitum_ui._decoders.ui import decode_ui
from daitum_ui._decoders.views import decode_view
from daitum_ui.ui_builder import UiBuilder

_done: set[str] = set()


def register_all() -> None:
    """Register every UI decoder. Idempotent — safe to call more than once."""
    if _done:
        return
    leaves.register()
    views.register()
    sections.register()
    register_decoder(UiBuilder, decode_ui)
    _done.add("registered")


__all__ = ["decode_ui", "decode_view", "register_all"]
