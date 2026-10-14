"""Reusable, service-free widgets used by the Auralume window."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QPalette
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget


class ElidedLabel(QLabel):
    """One-line text that can shrink, with the full value available to readers."""

    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setText(text)

    def setText(self, text):  # noqa: N802
        super().setText(text)
        self.setToolTip(text)
        self.setAccessibleName(text)

    def sizeHint(self):  # noqa: N802
        return QSize(160, self.fontMetrics().height() + 2)

    def minimumSizeHint(self):  # noqa: N802
        return QSize(0, self.fontMetrics().height() + 2)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        rect = self.contentsRect()
        visible = self.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideRight, rect.width())
        self.style().drawItemText(painter, rect, int(self.alignment()), self.palette(),
                                  self.isEnabled(), visible, QPalette.ColorRole.WindowText)


class CoverArt(QFrame):
    """Small original cover fallback, optionally displaying a local image."""

    def __init__(self, artwork: str = "", size: int = 54, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setObjectName("coverArt")
        self._pixmap = None
        self.set_artwork(artwork)

    def set_artwork(self, artwork: str) -> None:
        from PySide6.QtGui import QPixmap

        pixmap = QPixmap(artwork) if artwork else QPixmap()
        self._pixmap = pixmap if not pixmap.isNull() else None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt virtual method
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._pixmap:
            from PySide6.QtGui import QPainterPath

            path = QPainterPath()
            path.addRoundedRect(self.rect(), 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(self.rect(), self._pixmap)
            return
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#7548A8"))
        gradient.setColorAt(0.55, QColor("#3F497E"))
        gradient.setColorAt(1.0, QColor("#D79444"))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        painter.setPen(QColor("#FFF5E4"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "♪")


class TrackCard(QFrame):
    """A compact recommendation card that emits its track id on activation."""

    def __init__(self, track, activated, parent: QWidget | None = None):
        super().__init__(parent)
        self.track_id = str(getattr(track, "id", ""))
        self.setObjectName("trackCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 14)
        layout.setSpacing(9)
        layout.addWidget(CoverArt(str(getattr(track, "artwork", "")), 126, self))
        title = ElidedLabel(str(getattr(track, "title", "Sem título")))
        title.setObjectName("cardTitle")
        artist = ElidedLabel(str(getattr(track, "artist", "Artista desconhecido")))
        artist.setObjectName("mutedText")
        layout.addWidget(title)
        layout.addWidget(artist)
        self._activated = activated

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt virtual method
        if event.button() == Qt.MouseButton.LeftButton:
            self._activated(self.track_id)
        super().mousePressEvent(event)
