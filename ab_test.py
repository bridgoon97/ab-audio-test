#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A/B 音频主观测试工具（PySide6 GUI）。"""

import csv
import os
import random
import re
import sys
import threading
import time
import datetime as dt
import platform

import numpy as np
import sounddevice as sd
import soundfile as sf
from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import (QBrush, QColor, QDesktopServices, QFont,
                           QKeySequence, QPainter, QPen, QShortcut)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


APP_TITLE = 'A/B 音频主观测试'
AUDIO_EXTS = {'.wav', '.flac', '.mp3', '.ogg', '.aif', '.aiff'}
TAG_RE = re.compile(r'^(.+?)[ _.\-]([AaBb12])$')
MOS_MIN = 10
MOS_MAX = 50
MOS_DEFAULT = 30

STYLE_SHEET = '''
QWidget#page {
    background-color: #f6f7fb;
}
QStackedWidget {
    background: transparent;
}
QFrame#card {
    background-color: #ffffff;
    border: 1px solid #e7eaf3;
    border-radius: 18px;
}
QLabel {
    color: #111827;
    background: transparent;
}
QLabel#title {
    font-size: 27px;
    font-weight: 800;
}
QLabel#subtitle {
    color: #667085;
    font-size: 13px;
}
QLabel#eyebrow {
    color: #4f46e5;
    font-size: 12px;
    font-weight: 800;
}
QLabel#field {
    color: #667085;
    font-size: 12px;
    font-weight: 700;
}
QLabel#hint {
    color: #8b93a7;
    font-size: 12px;
}
QLabel#status {
    color: #16a34a;
    font-size: 16px;
    font-weight: 800;
}
QLabel#progressText {
    font-size: 17px;
    font-weight: 800;
}
QLabel#ratingTitle {
    font-size: 17px;
    font-weight: 800;
}
QLabel#resultText {
    color: #475467;
    font-size: 15px;
}
QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #d9deea;
    border-radius: 10px;
    padding: 10px 12px;
    color: #101828;
    min-height: 18px;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #4f46e5;
}
QComboBox::drop-down {
    width: 32px;
    border: none;
}
QPushButton {
    color: #344054;
    border: 1px solid #d0d5dd;
    border-radius: 10px;
    padding: 9px 16px;
    background-color: #ffffff;
    font-weight: 700;
}
QPushButton:hover {
    background-color: #f9fafb;
}
QPushButton:pressed {
    background-color: #f2f4f7;
}
QPushButton#primary {
    background-color: #4f46e5;
    border-color: #4f46e5;
    color: #ffffff;
    padding: 12px 24px;
    border-radius: 12px;
}
QPushButton#primary:hover {
    background-color: #4338ca;
}
QPushButton#primary:pressed {
    background-color: #3730a3;
}
QPushButton#primary:disabled {
    background-color: #c7d2fe;
    border-color: #c7d2fe;
}
QPushButton#secondary {
    background-color: #eef2ff;
    border-color: #eef2ff;
    color: #4f46e5;
    padding: 10px 22px;
    min-height: 20px;
    min-width: 72px;
}
QPushButton#secondary:hover {
    background-color: #e0e7ff;
}
QPushButton#secondary:pressed {
    background-color: #c7d2fe;
}
QPushButton#playA {
    background-color: #4f46e5;
    border-color: #4f46e5;
    color: #ffffff;
    border-radius: 14px;
    padding: 14px 20px;
    min-height: 44px;
    font-size: 17px;
    font-weight: 800;
}
QPushButton#playA:hover {
    background-color: #4338ca;
}
QPushButton#playA[active="true"] {
    background-color: #3730a3;
}
QPushButton#playB {
    background-color: #0d9488;
    border-color: #0d9488;
    color: #ffffff;
    border-radius: 14px;
    padding: 14px 20px;
    min-height: 44px;
    font-size: 17px;
    font-weight: 800;
}
QPushButton#playB:hover {
    background-color: #0f766e;
}
QPushButton#playB[active="true"] {
    background-color: #115e59;
}
QPushButton#rating {
    background-color: #f8fafc;
    border-color: #e2e8f0;
    padding: 10px;
    min-width: 58px;
    border-radius: 10px;
}
QPushButton#rating:checked {
    background-color: #4f46e5;
    border-color: #4f46e5;
    color: #ffffff;
}
QCheckBox {
    color: #344054;
    spacing: 8px;
}
QProgressBar {
    background-color: #eef2ff;
    border: none;
    border-radius: 4px;
    min-height: 8px;
    max-height: 8px;
}
QProgressBar::chunk {
    background-color: #4f46e5;
    border-radius: 4px;
}
QSlider::groove:horizontal {
    height: 6px;
    background-color: #e2e8f0;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background-color: #4f46e5;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
QSlider::handle:horizontal:hover {
    background-color: #4338ca;
}
QSlider::sub-page:horizontal {
    background-color: #c7d2fe;
    border-radius: 3px;
}
QLabel#mosValue {
    color: #4f46e5;
    font-size: 22px;
    font-weight: 800;
    min-width: 52px;
}
QLabel#mosHint {
    color: #8b93a7;
    font-size: 11px;
}
QLabel#timeLabel {
    color: #667085;
    font-size: 12px;
    font-weight: 600;
}
'''


def app_dir():
    """程序所在目录（兼容 PyInstaller 打包后的 exe）。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_pairs(folder):
    """扫描文件夹，按 _A/_B（或 _1/_2）后缀配对样本。"""
    groups = {}
    unmatched = []
    for name in sorted(os.listdir(folder)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in AUDIO_EXTS:
            continue
        match = TAG_RE.match(stem)
        if not match:
            unmatched.append(name)
            continue
        base, tag = match.group(1), match.group(2).upper()
        tag = 'A' if tag in ('A', '1') else 'B'
        groups.setdefault(base, {})[tag] = name
    pairs = []
    for base in sorted(groups):
        sample = groups[base]
        if 'A' in sample and 'B' in sample:
            pairs.append((base, sample['A'], sample['B']))
        else:
            unmatched.append(sample.get('A', sample.get('B')))
    return pairs, unmatched


class Player:
    """基于 PortAudio 回调流的播放器：支持 A/B 切换、循环、暂停与范围循环。"""

    def __init__(self):
        self.stream = None
        self.sr = None
        self.channels = None
        self.cur = None
        self.pos = 0
        self.loop = False
        self.paused = False
        self.range_start = 0
        self.range_end = 0
        self.volume = 1.0
        self.lock = threading.Lock()

    def play(self, data, sr, loop=False, start_frame=0):
        data = np.ascontiguousarray(data, dtype=np.float32)
        if data.ndim == 1:
            data = data[:, None]
        if len(data) == 0:
            return
        with self.lock:
            self.cur = data
            self.pos = max(0, min(start_frame, len(data) - 1))
            self.loop = loop
            self.paused = False
        self._ensure_stream(sr, data.shape[1])

    def set_volume(self, value):
        with self.lock:
            self.volume = max(0.0, min(1.0, value))

    def set_loop(self, loop):
        with self.lock:
            self.loop = loop

    def stop(self):
        with self.lock:
            self.cur = None
            self.pos = 0
            self.paused = False
            self.range_start = 0
            self.range_end = 0

    def is_playing(self):
        with self.lock:
            return self.cur is not None

    def is_paused(self):
        with self.lock:
            return self.paused

    def pause(self):
        with self.lock:
            self.paused = True

    def resume(self):
        with self.lock:
            self.paused = False

    def get_position(self):
        with self.lock:
            return self.pos

    def get_position_seconds(self):
        with self.lock:
            if self.sr:
                return self.pos / self.sr
            return 0.0

    def seek(self, frame):
        with self.lock:
            if self.cur is not None:
                self.pos = max(0, min(frame, len(self.cur) - 1))

    def set_range(self, start, end):
        with self.lock:
            self.range_start = max(0, start)
            self.range_end = max(start + 1, end)

    def clear_range(self):
        with self.lock:
            self.range_start = 0
            self.range_end = 0

    def _ensure_stream(self, sr, channels):
        if self.stream is not None and self.sr == sr and self.channels == channels:
            return
        self._close_stream()
        self.stream = sd.OutputStream(samplerate=sr, channels=channels,
                                      callback=self._callback)
        self.stream.start()
        self.sr = sr
        self.channels = channels

    def _callback(self, outdata, frames, time_info, status):
        with self.lock:
            current = self.cur
            if current is None or self.paused:
                outdata[:] = 0
                return
            length = len(current)
            vol = self.volume
            if self.range_end > self.range_start:
                range_len = self.range_end - self.range_start
                offset = self.pos - self.range_start
                idx = (np.arange(frames) + offset) % range_len + self.range_start
                outdata[:] = current[idx] * vol
                self.pos = int((offset + frames) % range_len + self.range_start)
            elif self.loop:
                idx = (np.arange(frames) + self.pos) % length
                outdata[:] = current[idx] * vol
                self.pos = int((self.pos + frames) % length)
            else:
                take = min(frames, length - self.pos)
                if take > 0:
                    outdata[:take] = current[self.pos:self.pos + take] * vol
                if take < frames:
                    outdata[take:] = 0
                    self.cur = None
                else:
                    self.pos += take

    def _close_stream(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
            self.sr = None
            self.channels = None

    def close(self):
        self.stop()
        self._close_stream()


class Card(QFrame):
    def __init__(self, parent=None, margins=(24, 24, 24, 24), spacing=14):
        super().__init__(parent)
        self.setObjectName('card')
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(*margins)
        self.layout.setSpacing(spacing)


class Page(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('page')


class TimelineWidget(QWidget):
    """可拖拽选区的音频时间轴（不显示波形）。"""

    rangeChanged = Signal(float, float)
    seekRequested = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40)
        self.setMouseTracking(True)
        self.duration = 0.0
        self.position = 0.0
        self.sel_start = -1.0
        self.sel_end = -1.0
        self._dragging = False
        self._drag_start_x = 0.0

    def set_duration(self, seconds):
        self.duration = max(seconds, 0.0)
        self.sel_start = -1.0
        self.sel_end = -1.0
        self.update()

    def set_position(self, seconds):
        self.position = max(0.0, min(seconds, self.duration))
        self.update()

    def clear_selection(self):
        self.sel_start = -1.0
        self.sel_end = -1.0
        self.update()

    def has_selection(self):
        return self.sel_start >= 0 and self.sel_end > self.sel_start + 0.05

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        track_y = h // 2 - 3
        track_h = 6
        margin = 6
        inner_w = w - margin * 2

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#e2e8f0'))
        painter.drawRoundedRect(margin, track_y, inner_w, track_h, 3, 3)

        if self.has_selection() and self.duration > 0:
            x1 = margin + int((self.sel_start / self.duration) * inner_w)
            x2 = margin + int((self.sel_end / self.duration) * inner_w)
            painter.setBrush(QColor('#4f46e5'))
            painter.drawRoundedRect(x1, track_y, max(x2 - x1, 4), track_h, 3, 3)

        if self.duration > 0:
            x = margin + int((self.position / self.duration) * inner_w)
            painter.setBrush(QColor('#4f46e5'))
            painter.drawEllipse(int(x) - 6, h // 2 - 6, 12, 12)

        painter.end()

    def _frame_from_x(self, x):
        margin = 6
        inner_w = self.width() - margin * 2
        ratio = max(0.0, min(1.0, (x - margin) / max(inner_w, 1)))
        return ratio * self.duration

    def mousePressEvent(self, event):
        self._dragging = True
        self._drag_start_x = event.position().x()

    def mouseMoveEvent(self, event):
        if self._dragging and self.duration > 0:
            x = event.position().x()
            frame = self._frame_from_x(x)
            if self.sel_start < 0:
                self.sel_start = frame
                self.sel_end = frame
            else:
                self.sel_end = max(frame, self.sel_start)
            self.update()

    def mouseReleaseEvent(self, event):
        if not self._dragging:
            return
        self._dragging = False
        x = event.position().x()
        moved = abs(x - self._drag_start_x) > 5
        if moved and self.has_selection():
            self.rangeChanged.emit(self.sel_start, self.sel_end)
        else:
            self.sel_start = -1.0
            self.sel_end = -1.0
            self.update()
            self.seekRequested.emit(self._frame_from_x(x))


class SetupPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pairs = []
        self.unmatched = []
        self.devices = []
        self._build()
        self._load_devices()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 30, 32, 32)
        root.setSpacing(18)

        heading = QVBoxLayout()
        heading.setSpacing(5)
        eyebrow = QLabel('设置测试')
        eyebrow.setObjectName('eyebrow')
        title = QLabel('A/B 音频主观测试')
        title.setObjectName('title')
        subtitle = QLabel('双盲听音打分 · 适用于编解码器 / 算法 / 处理链对比等主观评价')
        subtitle.setObjectName('subtitle')
        heading.addWidget(eyebrow)
        heading.addWidget(title)
        heading.addWidget(subtitle)
        root.addLayout(heading)

        folder_card = Card(self, margins=(26, 24, 26, 24))
        folder_label = QLabel('音频文件夹')
        folder_label.setObjectName('field')
        folder_row = QHBoxLayout()
        folder_row.setSpacing(10)
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText('选择包含成对音频样本的文件夹')
        browse_btn = QPushButton('浏览…')
        browse_btn.clicked.connect(self.browse)
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(browse_btn)
        self.info_label = QLabel('尚未选择文件夹')
        self.info_label.setObjectName('hint')
        hint_label = QLabel('样本命名规则：同一对比项以 _A/_B 结尾（也支持 _1/_2），例如 guitar_A.wav / guitar_B.wav。')
        hint_label.setObjectName('hint')
        hint_label.setWordWrap(True)
        folder_card.layout.addWidget(folder_label)
        folder_card.layout.addLayout(folder_row)
        folder_card.layout.addWidget(self.info_label)
        folder_card.layout.addWidget(hint_label)
        root.addWidget(folder_card)

        settings_card = Card(self, margins=(26, 24, 26, 24))
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(6)
        listener_label = QLabel('试听者')
        listener_label.setObjectName('field')
        self.listener_edit = QLineEdit(os.environ.get('USERNAME', ''))
        self.listener_edit.setPlaceholderText('用于结果文件命名')
        device_label = QLabel('输出设备')
        device_label.setObjectName('field')
        self.device_box = QComboBox()
        grid.addWidget(listener_label, 0, 0)
        grid.addWidget(self.listener_edit, 1, 0)
        grid.addWidget(device_label, 0, 1)
        grid.addWidget(self.device_box, 1, 1)
        settings_card.layout.addLayout(grid)
        root.addWidget(settings_card)

        options_card = Card(self, margins=(26, 20, 26, 20))
        self.shuffle_box = QCheckBox('随机打乱样本顺序')
        self.shuffle_box.setChecked(True)
        self.blind_box = QCheckBox('双盲：每个样本随机交换 A / B（结果文件中记录真实对应关系）')
        self.blind_box.setChecked(True)
        options_card.layout.addWidget(self.shuffle_box)
        options_card.layout.addWidget(self.blind_box)
        root.addWidget(options_card)

        actions = QHBoxLayout()
        actions.addStretch(1)
        start_btn = QPushButton('开始测试 →')
        start_btn.setObjectName('primary')
        start_btn.setMinimumWidth(160)
        start_btn.clicked.connect(self.start_test)
        actions.addWidget(start_btn)
        root.addLayout(actions)
        root.addStretch(1)

    def _load_devices(self):
        names = ['系统默认']
        try:
            for idx, device in enumerate(sd.query_devices()):
                if device.get('max_output_channels', 0) > 0:
                    self.devices.append(idx)
                    names.append(device['name'])
        except Exception:
            pass
        self.device_box.clear()
        self.device_box.addItems(names)
        self.device_box.setCurrentIndex(0)

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, '选择包含音频样本的文件夹')
        if not folder:
            return
        self.folder_edit.setText(folder)
        self.pairs, self.unmatched = find_pairs(folder)
        msg = f'找到 {len(self.pairs)} 对样本'
        if self.unmatched:
            msg += f'（{len(self.unmatched)} 个文件未按规则配对，将被忽略）'
        self.info_label.setText(msg)

    def start_test(self):
        if not self.pairs:
            QMessageBox.warning(
                self, '提示',
                '请先选择包含成对样本的文件夹。\n\n样本需成对命名，例如 guitar_A.wav / guitar_B.wav')
            return
        folder = self.folder_edit.text().strip()
        listener = self.listener_edit.text().strip() or 'anonymous'
        trials = []
        for base, file_a, file_b in self.pairs:
            path_a = os.path.join(folder, file_a)
            path_b = os.path.join(folder, file_b)
            if self.blind_box.isChecked() and random.random() < 0.5:
                path_a, path_b = path_b, path_a
            trials.append({
                'base': base,
                'pathA': path_a,
                'pathB': path_b,
                'fileA': os.path.basename(path_a),
                'fileB': os.path.basename(path_b),
            })
        if self.shuffle_box.isChecked():
            random.shuffle(trials)
        device_index = self.device_box.currentIndex()
        if device_index > 0:
            sd.default.device = self.devices[device_index - 1]
        cfg = {
            'listener': listener,
            'trials': trials,
            'results_dir': os.path.join(app_dir(), 'results'),
        }
        self.app.test_page.start(cfg)
        self.app.show_page(self.app.test_page)


class TestPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.player = Player()
        self.cfg = None
        self.trials = []
        self.index = 0
        self.buf = {}
        self.file = None
        self.writer = None
        self.result_path = ''
        self.playing = None
        self.trial_start = 0.0
        self.range_start_sec = 0.0
        self.range_end_sec = 0.0
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(50)
        self.poll_timer.timeout.connect(self._poll)
        self._build()
        self._add_shortcuts()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 30, 32, 32)
        root.setSpacing(12)

        progress_card = Card(self, margins=(24, 18, 24, 18), spacing=10)
        self.progress_label = QLabel('')
        self.progress_label.setObjectName('progressText')
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        progress_card.layout.addWidget(self.progress_label)
        progress_card.layout.addWidget(self.progress)
        root.addWidget(progress_card)

        play_card = Card(self, margins=(24, 20, 24, 20), spacing=10)
        play_row = QHBoxLayout()
        play_row.setSpacing(14)
        self.btn_a = QPushButton('▶ 播放 A')
        self.btn_a.setObjectName('playA')
        self.btn_b = QPushButton('▶ 播放 B')
        self.btn_b.setObjectName('playB')
        for button in (self.btn_a, self.btn_b):
            button.setFocusPolicy(Qt.NoFocus)
        self.btn_a.clicked.connect(lambda: self.play('A'))
        self.btn_b.clicked.connect(lambda: self.play('B'))
        play_row.addWidget(self.btn_a)
        play_row.addWidget(self.btn_b)
        self.play_label = QLabel(' ')
        self.play_label.setObjectName('status')
        self.play_label.setAlignment(Qt.AlignCenter)

        self.timeline = TimelineWidget()
        self.timeline.rangeChanged.connect(self._on_range_changed)
        self.timeline.seekRequested.connect(self._on_seek)
        self.timeline.setMinimumHeight(44)
        time_row = QHBoxLayout()
        time_row.setContentsMargins(4, 0, 4, 0)
        self.time_current = QLabel('00:00')
        self.time_current.setObjectName('timeLabel')
        self.time_total = QLabel('00:00')
        self.time_total.setObjectName('timeLabel')
        self.time_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        time_row.addWidget(self.time_current)
        time_row.addStretch(1)
        time_row.addWidget(self.time_total)

        controls = QHBoxLayout()
        self.btn_pause = QPushButton('⏸ 暂停')
        self.btn_pause.setObjectName('secondary')
        self.btn_pause.setEnabled(False)
        self.btn_pause.setFocusPolicy(Qt.NoFocus)
        self.btn_pause.clicked.connect(self.toggle_pause)
        stop_btn = QPushButton('⏹ 停止')
        stop_btn.setObjectName('secondary')
        stop_btn.setFocusPolicy(Qt.NoFocus)
        stop_btn.clicked.connect(self.stop)
        self.loop_box = QCheckBox('循环播放 (L)')
        self.loop_box.toggled.connect(self.player.set_loop)
        volume_label = QLabel('音量')
        volume_label.setObjectName('hint')
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setFocusPolicy(Qt.NoFocus)
        self.volume_slider.valueChanged.connect(
            lambda v: self.player.set_volume(v / 100.0))
        clear_btn = QPushButton('清除选区')
        clear_btn.setObjectName('secondary')
        clear_btn.setFocusPolicy(Qt.NoFocus)
        clear_btn.clicked.connect(self._clear_range)
        controls.addWidget(self.btn_pause)
        controls.addWidget(stop_btn)
        controls.addWidget(self.loop_box)
        controls.addWidget(volume_label)
        controls.addWidget(self.volume_slider)
        controls.addWidget(clear_btn)
        controls.addStretch(1)
        shortcut_hint = QLabel('快捷键：A / B 播放 · 空格 停止 · L 循环 · 回车 下一项 · 时间轴拖拽选区循环')
        shortcut_hint.setObjectName('hint')
        shortcut_hint.setAlignment(Qt.AlignCenter)
        play_card.layout.addLayout(play_row)
        play_card.layout.addWidget(self.play_label)
        play_card.layout.addWidget(self.timeline)
        play_card.layout.addLayout(time_row)
        play_card.layout.addLayout(controls)
        play_card.layout.addWidget(shortcut_hint)
        root.addWidget(play_card)

        rating_card = Card(self, margins=(24, 20, 24, 20), spacing=14)
        rating_grid = QGridLayout()
        rating_grid.setHorizontalSpacing(16)
        self.rated_a = False
        self.rated_b = False
        self._updating_sliders = False
        self._make_mos_slider(rating_grid, 0, '样本 A 音质')
        self._make_mos_slider(rating_grid, 1, '样本 B 音质')
        rating_card.layout.addLayout(rating_grid)
        root.addWidget(rating_card, 1)

        bottom_card = Card(self, margins=(24, 18, 24, 18), spacing=8)
        comment_label = QLabel('备注（可选）')
        comment_label.setObjectName('field')
        self.comment_edit = QLineEdit()
        self.comment_edit.setPlaceholderText('可记录明显的噪声、失真、响度差异等')
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)
        self.btn_next = QPushButton('下一项 →')
        self.btn_next.setObjectName('primary')
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self.next_trial)
        bottom_row.addWidget(self.btn_next, 0, Qt.AlignRight)
        bottom_card.layout.addWidget(comment_label)
        bottom_card.layout.addWidget(self.comment_edit)
        bottom_card.layout.addLayout(bottom_row)
        root.addWidget(bottom_card)

    def _make_mos_slider(self, grid, column, title):
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(10)
        label = QLabel(title)
        label.setObjectName('ratingTitle')
        value_row = QHBoxLayout()
        value_row.setSpacing(12)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(MOS_MIN, MOS_MAX)
        slider.setValue(MOS_DEFAULT)
        slider.setFocusPolicy(Qt.NoFocus)
        value_label = QLabel('未评分')
        value_label.setObjectName('mosValue')
        value_label.setAlignment(Qt.AlignCenter)
        value_row.addWidget(slider, 1)
        value_row.addWidget(value_label)
        hint = QLabel('拖动滑块打分（1.0 – 5.0）')
        hint.setObjectName('mosHint')
        if column == 0:
            self.slider_a = slider
            self.label_a = value_label
            slider.valueChanged.connect(self._on_slider_a_changed)
        else:
            self.slider_b = slider
            self.label_b = value_label
            slider.valueChanged.connect(self._on_slider_b_changed)
        container_layout.addWidget(label)
        container_layout.addLayout(value_row)
        container_layout.addWidget(hint)
        grid.addWidget(container, 0, column)

    def _on_slider_a_changed(self, value):
        if self._updating_sliders:
            return
        self.rated_a = True
        self.label_a.setText(f'{value / 10:.1f}')
        self._check_ready()

    def _on_slider_b_changed(self, value):
        if self._updating_sliders:
            return
        self.rated_b = True
        self.label_b.setText(f'{value / 10:.1f}')
        self._check_ready()

    def _add_shortcuts(self):
        shortcuts = {
            'A': self._shortcut_play_a,
            'B': self._shortcut_play_b,
            ' ': self._shortcut_stop,
            'L': self._shortcut_loop,
            'Return': self._shortcut_next,
            'Enter': self._shortcut_next,
            'Esc': self._shortcut_stop,
        }
        self._shortcuts = []
        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.WidgetWithChildrenShortcut)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)

    def _shortcut_play_a(self):
        if not self.comment_edit.hasFocus():
            self.play('A')

    def _shortcut_play_b(self):
        if not self.comment_edit.hasFocus():
            self.play('B')

    def _shortcut_stop(self):
        if not self.comment_edit.hasFocus():
            self.stop()

    def _shortcut_loop(self):
        if not self.comment_edit.hasFocus():
            self.loop_box.toggle()

    def _shortcut_next(self):
        if self.btn_next.isEnabled():
            self.next_trial()

    def start(self, cfg):
        self.cfg = cfg
        self.trials = cfg['trials']
        self.index = 0
        if self.file is not None:
            try:
                self.file.close()
            except Exception:
                pass
        os.makedirs(cfg['results_dir'], exist_ok=True)
        safe = re.sub(r'[\\/:*?"<>|]', '_', cfg['listener']).strip() or 'anonymous'
        filename = dt.datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + safe + '.csv'
        self.result_path = os.path.join(cfg['results_dir'], filename)
        self.file = open(self.result_path, 'w', newline='', encoding='utf-8-sig')
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            '时间', '试听者', '序号', '样本', 'A=实际文件', 'B=实际文件',
            'A MOS分', 'B MOS分', '备注', '用时(秒)',
        ])
        self.file.flush()
        self.show_trial()

    def show_trial(self):
        self.player.stop()
        self.playing = None
        self.poll_timer.stop()
        self._update_play_state()
        self._clear_range()
        self._updating_sliders = True
        self.slider_a.setValue(MOS_DEFAULT)
        self.slider_b.setValue(MOS_DEFAULT)
        self._updating_sliders = False
        self.rated_a = False
        self.rated_b = False
        self.label_a.setText('未评分')
        self.label_b.setText('未评分')
        self.comment_edit.clear()
        self.btn_next.setEnabled(False)
        while self.index < len(self.trials):
            trial = self.trials[self.index]
            buffers = {}
            ok = True
            for key, path in (('A', trial['pathA']), ('B', trial['pathB'])):
                try:
                    data, sr = sf.read(path, dtype='float32', always_2d=True)
                    buffers[key] = (data, sr)
                except Exception as exc:
                    ok = False
                    QMessageBox.warning(
                        self, '无法读取音频',
                        f'文件：{path}\n\n{exc}\n\n该样本对将被跳过。')
                    break
            if ok:
                self.buf = buffers
                break
            self.index += 1
        if self.index >= len(self.trials):
            self.finish()
            return
        trial = self.trials[self.index]
        self.trial_start = time.time()
        duration_a = len(self.buf['A'][0]) / self.buf['A'][1]
        duration_b = len(self.buf['B'][0]) / self.buf['B'][1]
        total = max(duration_a, duration_b)
        self.timeline.set_duration(total)
        self.time_total.setText(self._format_time(total))
        self.time_current.setText('00:00')
        self.progress.setMaximum(len(self.trials))
        self.progress.setValue(self.index)
        self.progress_label.setText(f'样本 {self.index + 1} / {len(self.trials)} · {trial["base"]}')

    def play(self, which):
        buffer = self.buf.get(which)
        if not buffer:
            return
        data, sr = buffer
        pos_sec = 0.0
        if self.playing and self.playing in self.buf and self.playing != which:
            old_data, old_sr = self.buf[self.playing]
            old_pos = self.player.get_position()
            pos_sec = old_pos / old_sr if old_sr else 0.0
        elif self.playing == which and self.player.get_position() > 0:
            pos_sec = self.player.get_position() / sr
        start_frame = int(pos_sec * sr) if pos_sec > 0 else 0
        start_frame = max(0, min(start_frame, len(data) - 1))
        try:
            self.player.play(data, sr, self.loop_box.isChecked(), start_frame)
        except Exception as exc:
            QMessageBox.critical(self, '播放失败', str(exc))
            return
        self.playing = which
        self._apply_range_to_player()
        self._update_play_state()
        self.poll_timer.start()
        self.btn_pause.setText('⏸ 暂停')
        self.btn_pause.setEnabled(True)
        self.setFocus()

    def toggle_pause(self):
        if self.player.is_paused():
            self.player.resume()
            self.btn_pause.setText('⏸ 暂停')
        else:
            self.player.pause()
            self.btn_pause.setText('▶ 继续')

    def stop(self):
        self.player.stop()
        self.playing = None
        self._update_play_state()
        self.btn_pause.setText('⏸ 暂停')
        self.btn_pause.setEnabled(False)

    def _on_seek(self, seconds):
        if self.playing and self.playing in self.buf:
            data, sr = self.buf[self.playing]
            frame = int(seconds * sr)
            self.player.seek(frame)

    def _on_range_changed(self, start_sec, end_sec):
        self.range_start_sec = start_sec
        self.range_end_sec = end_sec
        self._apply_range_to_player()

    def _apply_range_to_player(self):
        if self.playing and self.range_end_sec > self.range_start_sec and self.playing in self.buf:
            data, sr = self.buf[self.playing]
            start = int(self.range_start_sec * sr)
            end = min(int(self.range_end_sec * sr), len(data))
            self.player.set_range(start, end)

    def _clear_range(self):
        self.range_start_sec = 0.0
        self.range_end_sec = 0.0
        self.timeline.clear_selection()
        self.player.clear_range()

    def _check_ready(self):
        ready = self.rated_a and self.rated_b
        self.btn_next.setEnabled(ready)

    def next_trial(self):
        if not (self.rated_a and self.rated_b):
            return
        score_a = self.slider_a.value() / 10
        score_b = self.slider_b.value() / 10
        self.player.stop()
        self.playing = None
        self.poll_timer.stop()
        trial = self.trials[self.index]
        elapsed = round(time.time() - self.trial_start, 1)
        self.writer.writerow([
            dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            self.cfg['listener'],
            self.index + 1,
            trial['base'],
            trial['fileA'],
            trial['fileB'],
            score_a,
            score_b,
            self.comment_edit.text().strip(),
            elapsed,
        ])
        self.file.flush()
        self.index += 1
        if self.index >= len(self.trials):
            self.finish()
        else:
            self.show_trial()

    def finish(self):
        self.player.stop()
        self.poll_timer.stop()
        if self.file is not None:
            self.file.close()
            self.file = None
        self.app.finish_page.set_result(
            self.result_path, len(self.trials), self.cfg['listener'])
        self.app.show_page(self.app.finish_page)

    def close_player(self):
        self.poll_timer.stop()
        self.player.close()

    def _update_play_state(self):
        self.btn_a.setProperty('active', self.playing == 'A')
        self.btn_b.setProperty('active', self.playing == 'B')
        for button in (self.btn_a, self.btn_b):
            button.style().unpolish(button)
            button.style().polish(button)
        if self.playing:
            self.play_label.setText(f'正在播放：{self.playing}')
        else:
            self.play_label.setText(' ')

    def _poll(self):
        if self.player.is_playing():
            pos = self.player.get_position_seconds()
            self.timeline.set_position(pos)
            self.time_current.setText(self._format_time(pos))
            self.btn_pause.setEnabled(True)
            return
        self.playing = None
        self._update_play_state()
        self.poll_timer.stop()
        self.btn_pause.setText('⏸ 暂停')
        self.btn_pause.setEnabled(False)

    @staticmethod
    def _format_time(seconds):
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f'{minutes:02d}:{secs:02d}'


class FinishPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.path = ''
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 30, 32, 32)
        root.addStretch(1)
        card = Card(self, margins=(32, 34, 32, 32), spacing=18)
        title = QLabel('测试完成')
        title.setObjectName('title')
        title.setStyleSheet('color: #16a34a;')
        self.result_label = QLabel('')
        self.result_label.setObjectName('resultText')
        self.result_label.setWordWrap(True)
        buttons = QHBoxLayout()
        open_btn = QPushButton('打开结果文件夹')
        open_btn.setObjectName('primary')
        open_btn.clicked.connect(self.open_folder)
        again_btn = QPushButton('再测一轮')
        again_btn.setObjectName('secondary')
        again_btn.clicked.connect(lambda: self.app.show_page(self.app.setup_page))
        buttons.addWidget(open_btn)
        buttons.addWidget(again_btn)
        buttons.addStretch(1)
        card.layout.addWidget(title)
        card.layout.addWidget(self.result_label)
        card.layout.addLayout(buttons)
        root.addWidget(card)
        root.addStretch(1)

    def set_result(self, path, count, listener):
        self.path = path
        self.result_label.setText(
            f'试听者：{listener}\n共评价 {count} 对样本\n结果已保存到：{path}')

    def open_folder(self):
        folder = os.path.dirname(self.path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(940, 780)
        self.setMinimumSize(840, 620)
        self._build_ui()
        self.setStyleSheet(STYLE_SHEET)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName('page')
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget(central)
        self.setup_page = SetupPage(self.stack, self)
        self.test_page = TestPage(self.stack, self)
        self.finish_page = FinishPage(self.stack, self)
        for page in (self.setup_page, self.test_page, self.finish_page):
            self.stack.addWidget(page)
        layout.addWidget(self.stack)
        self.setCentralWidget(central)
        self.stack.setCurrentWidget(self.setup_page)

    def show_page(self, page):
        self.stack.setCurrentWidget(page)

    def closeEvent(self, event):
        if self.test_page.file is not None and not QMessageBox.question(
                self, '退出确认',
                '测试尚未完成，已完成部分的评分已保存。\n确定要退出吗？',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            event.ignore()
            return
        try:
            self.test_page.close_player()
        except Exception:
            pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font_family = {
        'Windows': 'Microsoft YaHei UI',
        'Darwin': 'PingFang SC',
    }.get(platform.system(), 'Noto Sans CJK SC')
    app.setFont(QFont(font_family, 10))
    window = App()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
