import math

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor, QPixmap, QPainter, QBrush, QPen, QPainterPath

from .settings import settings


def make_tray_icon():
    accent = '#60a5fa' if settings.theme == 'dark' else '#4169e1'
    bg     = '#111111' if settings.theme == 'dark' else '#f5f0eb'
    px = QPixmap(22, 22)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(QColor(accent)))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(3, 5, 16, 15, 2, 2)
    p.setBrush(QBrush(QColor(bg)))
    p.drawRoundedRect(7, 3, 8, 5, 2, 2)
    p.setBrush(QBrush(QColor(accent)))
    p.drawRect(8, 4, 6, 3)
    p.setBrush(QBrush(QColor(bg)))
    p.drawRect(6, 10, 10, 2)
    p.drawRect(6, 14, 10, 2)
    p.end()
    return QIcon(px)


def make_pin_button_icon(pinned=False):
    px = QPixmap(16, 16)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    color = QColor('#ffd76b' if pinned else '#e3b341')
    p.setPen(QPen(color, 1.0))
    p.setBrush(QBrush(color) if pinned else Qt.NoBrush)

    cx, cy = 8.0, 7.5
    R, r = 6.5, 2.7
    path = QPainterPath()
    for i in range(5):
        outer_a = math.radians(-90 + i * 72)
        inner_a = math.radians(-90 + 36 + i * 72)
        ox, oy = cx + R * math.cos(outer_a), cy + R * math.sin(outer_a)
        ix, iy = cx + r * math.cos(inner_a), cy + r * math.sin(inner_a)
        if i == 0:
            path.moveTo(ox, oy)
        else:
            path.lineTo(ox, oy)
        path.lineTo(ix, iy)
    path.closeSubpath()
    p.drawPath(path)
    p.end()
    return QIcon(px)


def make_copy_button_icon():
    accent = '#60a5fa' if settings.theme == 'dark' else '#4169e1'
    px = QPixmap(16, 16)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor(accent))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(5, 3, 7, 8, 1, 1)
    p.drawRoundedRect(3, 5, 7, 8, 1, 1)
    p.end()
    return QIcon(px)
