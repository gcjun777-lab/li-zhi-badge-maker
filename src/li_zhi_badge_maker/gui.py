from __future__ import annotations

import io
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .engine import render_badge, export_badge
from .models import BadgeRecord, calculate_days_from_join_date, infer_name_from_path
from .project_io import load_project, save_project


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.record: BadgeRecord | None = None
        self.current_project_path: Path | None = None
        self._loading_form = False

        self.setWindowTitle("离职厂牌制作助手")
        self.resize(1120, 760)
        self._build_ui()
        self._build_actions()

    def _build_ui(self) -> None:
        container = QWidget(self)
        self.setCentralWidget(container)
        root_layout = QVBoxLayout(container)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        root_layout.addWidget(splitter)

        editor_panel = QWidget(self)
        editor_layout = QVBoxLayout(editor_panel)
        form = QFormLayout()

        choose_button = QPushButton("选择图片文件")
        choose_button.clicked.connect(self.choose_image)
        clear_button = QPushButton("清空当前文件")
        clear_button.clicked.connect(self.clear_record)

        self.image_path_label = QLabel("-")
        self.image_path_label.setWordWrap(True)
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._sync_form_to_record)
        self.join_date_edit = QDateEdit()
        self.join_date_edit.setCalendarPopup(True)
        self.join_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.join_date_edit.setDate(QDate.currentDate())
        self.join_date_edit.dateChanged.connect(self._on_join_date_changed)
        self.days_value_label = QLabel("-")
        self.output_edit = QLineEdit()
        self.output_edit.textChanged.connect(self._sync_form_to_record)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.3, 2.5)
        self.scale_spin.setSingleStep(0.05)
        self.scale_spin.setValue(1.0)
        self.scale_spin.valueChanged.connect(self._sync_form_to_record)

        self.x_spin = QSpinBox()
        self.x_spin.setRange(-200, 200)
        self.x_spin.valueChanged.connect(self._sync_form_to_record)

        self.y_spin = QSpinBox()
        self.y_spin.setRange(-200, 200)
        self.y_spin.valueChanged.connect(self._sync_form_to_record)

        editor_layout.addWidget(choose_button)
        editor_layout.addWidget(clear_button)
        form.addRow("图片路径", self.image_path_label)
        form.addRow("姓名", self.name_edit)
        form.addRow("入职日期", self.join_date_edit)
        form.addRow("在职天数", self.days_value_label)
        form.addRow("输出文件名", self.output_edit)
        form.addRow("缩放比例", self.scale_spin)
        form.addRow("X 偏移", self.x_spin)
        form.addRow("Y 偏移", self.y_spin)

        refresh_button = QPushButton("刷新预览")
        refresh_button.clicked.connect(self.refresh_preview)
        editor_layout.addLayout(form)
        editor_layout.addWidget(refresh_button)
        editor_layout.addStretch(1)
        splitter.addWidget(editor_panel)

        preview_panel = QWidget(self)
        preview_layout = QVBoxLayout(preview_panel)
        preview_label = QLabel("预览")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image = QLabel("选择图片后显示预览")
        self.preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image.setMinimumWidth(360)
        self.preview_image.setStyleSheet("background:#f4f4f4;border:1px solid #d8d8d8;")
        export_button = QPushButton("导出当前图片")
        export_button.clicked.connect(self.export_current)
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_image, stretch=1)
        preview_layout.addWidget(export_button)
        splitter.addWidget(preview_panel)
        splitter.setSizes([430, 520])

    def _build_actions(self) -> None:
        toolbar = QToolBar("主工具栏", self)
        self.addToolBar(toolbar)

        open_action = QAction("打开工程", self)
        open_action.triggered.connect(self.open_project)
        save_action = QAction("保存工程", self)
        save_action.triggered.connect(self.save_project_file)
        save_as_action = QAction("另存工程", self)
        save_as_action.triggered.connect(lambda: self.save_project_file(save_as=True))
        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addAction(save_as_action)

    def choose_image(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "选择人物图片",
            "",
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if not selected:
            return
        path = Path(selected)
        self.record = BadgeRecord(
            image_path=str(path),
            name=infer_name_from_path(path),
            join_date=date.today().isoformat(),
            days="0",
            output_name=f"{infer_name_from_path(path)}-离职厂牌-.png",
        )
        self._load_record_into_form()

    def _load_record_into_form(self) -> None:
        self._loading_form = True
        record = self.record
        if record is None:
            self._loading_form = False
            self._clear_form()
            return
        self.image_path_label.setText(record.image_path)
        self.name_edit.setText(record.name)
        if record.join_date:
            self.join_date_edit.setDate(QDate.fromString(record.join_date, "yyyy-MM-dd"))
        else:
            self.join_date_edit.setDate(QDate.currentDate())
        self.days_value_label.setText(record.days or "-")
        self.output_edit.setText(record.output_name)
        self.scale_spin.setValue(record.scale_adjust)
        self.x_spin.setValue(record.x_offset)
        self.y_spin.setValue(record.y_offset)
        self._loading_form = False
        self.refresh_preview()

    def _clear_form(self) -> None:
        self._loading_form = True
        self.image_path_label.setText("-")
        self.name_edit.clear()
        self.join_date_edit.setDate(QDate.currentDate())
        self.days_value_label.setText("-")
        self.output_edit.clear()
        self.scale_spin.setValue(1.0)
        self.x_spin.setValue(0)
        self.y_spin.setValue(0)
        self._loading_form = False
        self.preview_image.setText("选择图片后显示预览")
        self.preview_image.setPixmap(QPixmap())

    def _sync_form_to_record(self) -> None:
        if self._loading_form:
            return
        record = self.record
        if not record:
            return
        record.name = self.name_edit.text().strip()
        record.join_date = self.join_date_edit.date().toString("yyyy-MM-dd")
        record.days = calculate_days_from_join_date(record.join_date)
        self.days_value_label.setText(record.days or "-")
        record.output_name = self.output_edit.text().strip()
        record.scale_adjust = self.scale_spin.value()
        record.x_offset = self.x_spin.value()
        record.y_offset = self.y_spin.value()
        if not record.output_name:
            record.output_name = f"{record.name or '未命名'}-离职厂牌-.png"
            self._loading_form = True
            self.output_edit.setText(record.output_name)
            self._loading_form = False
        self.refresh_preview()

    def _on_join_date_changed(self) -> None:
        if self._loading_form:
            return
        record = self.record
        if not record:
            return
        record.join_date = self.join_date_edit.date().toString("yyyy-MM-dd")
        record.days = calculate_days_from_join_date(record.join_date)
        self.days_value_label.setText(record.days or "-")
        self._sync_form_to_record()

    def refresh_preview(self) -> None:
        record = self.record
        if not record:
            return
        try:
            image = render_badge(record)
        except Exception as exc:  # pragma: no cover - GUI 提示逻辑
            QMessageBox.critical(self, "预览失败", str(exc))
            return

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")
        scaled = pixmap.scaled(
            420,
            540,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_image.setPixmap(scaled)
        self.preview_image.setText("")

    def clear_record(self) -> None:
        self.record = None
        self._clear_form()

    def export_current(self) -> None:
        record = self.record
        if not record:
            QMessageBox.information(self, "没有记录", "请先选择图片。")
            return
        suggested = record.output_name or f"{record.name or '未命名'}-离职厂牌-.png"
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "导出当前图片",
            suggested,
            "PNG Files (*.png)",
        )
        if not selected:
            return
        target = Path(selected)
        if target.suffix.lower() != ".png":
            target = target.with_suffix(".png")
        try:
            image = render_badge(record)
            image.save(target)
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return
        record.output_name = target.name
        self._loading_form = True
        self.output_edit.setText(record.output_name)
        self._loading_form = False
        QMessageBox.information(self, "导出完成", f"已导出到：\n{target}")

    def save_project_file(self, save_as: bool = False) -> None:
        if not self.record:
            QMessageBox.information(self, "没有记录", "请先选择图片或打开工程。")
            return
        if save_as or self.current_project_path is None:
            selected, _ = QFileDialog.getSaveFileName(self, "保存工程", "", "JSON Files (*.json)")
            if not selected:
                return
            self.current_project_path = Path(selected)
        save_project(self.current_project_path, [self.record])
        QMessageBox.information(self, "保存成功", f"工程已保存到：\n{self.current_project_path}")

    def open_project(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "打开工程", "", "JSON Files (*.json)")
        if not selected:
            return
        records = load_project(selected)
        self.current_project_path = Path(selected)
        self.record = records[0] if records else None
        self._load_record_into_form()


def run_gui() -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
