from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtGui")

from app.ui import MainWindow


class _StubCombo:
    def __init__(self, data):
        self._data = data

    def currentData(self):
        return self._data


class _StubWidget:
    def __init__(self):
        self.visible = True

    def setVisible(self, visible: bool) -> None:
        self.visible = visible


class _StubSearch:
    def __init__(self):
        self.focused = False

    def setFocus(self) -> None:
        self.focused = True


def test_should_collapse_selector_depends_on_selection_and_scroll_threshold() -> None:
    window = MainWindow.__new__(MainWindow)
    window.school_combo = _StubCombo({"school_name": "Bluewater"})

    assert window._should_collapse_selector(40) is False
    assert window._should_collapse_selector(41) is True

    window.school_combo = _StubCombo(None)
    assert window._should_collapse_selector(100) is False


def test_set_selector_collapsed_toggles_toolbar_visibility_without_resetting_school() -> None:
    window = MainWindow.__new__(MainWindow)
    selected = {"school_name": "Bluewater"}
    window.school_combo = _StubCombo(selected)
    window.selector_toolbar = _StubWidget()
    window.collapsed_selector_bar = _StubWidget()

    window._set_selector_collapsed(True)

    assert window.selector_collapsed is True
    assert window.selector_toolbar.visible is False
    assert window.collapsed_selector_bar.visible is True
    assert window.school_combo.currentData() == selected


def test_change_school_button_expands_toolbar_and_focuses_search() -> None:
    window = MainWindow.__new__(MainWindow)
    window.selector_toolbar = _StubWidget()
    window.collapsed_selector_bar = _StubWidget()
    window.search_box = _StubSearch()

    window._set_selector_collapsed(True)
    window._on_change_school_clicked()

    assert window.selector_collapsed is False
    assert window.selector_toolbar.visible is True
    assert window.collapsed_selector_bar.visible is False
    assert window.search_box.focused is True
