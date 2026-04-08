from __future__ import annotations

import io
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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
from .models import BadgeRecord, DEFAULT_SUBHEADLINE, build_headline, infer_name_from_path
from .project_io import load_project, save_project


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[BadgeRecord] = []
        self.current_project_path: Path | None = None
        self._loading_form = False

        self.setWindowTitle("离职厂牌制作助手")
        self.resize(1280, 760)
        self._build_ui()
        self._build_actions()

    def _build_ui(self) -> None:
        container = QWidget(self)
        self.setCentralWidget(container)
        root_layout = QVBoxLayout(container)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        root_layout.addWidget(splitter)

        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        import_button = QPushButton("导入图片文件夹")
        import_button.clicked.connect(self.import_folder)
        remove_button = QPushButton("删除当前记录")
        remove_button.clicked.connect(self.remove_current_record)
        self.list_widget = QListWidget(self)
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        left_layout.addWidget(import_button)
        left_layout.addWidget(remove_button)
        left_layout.addWidget(self.list_widget, stretch=1)
        splitter.addWidget(left_panel)

        editor_panel = QWidget(self)
        editor_layout = QVBoxLayout(editor_panel)
        form = QFormLayout()

        self.image_path_label = QLabel("-")
        self.image_path_label.setWordWrap(True)
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._sync_form_to_record)
        self.days_edit = QLineEdit()
        self.days_edit.textChanged.connect(self._on_days_changed)
        self.headline_edit = QLineEdit()
        self.headline_edit.textChanged.connect(self._sync_form_to_record)
        self.subheadline_edit = QLineEdit(DEFAULT_SUBHEADLINE)
        self.subheadline_edit.textChanged.connect(self._sync_form_to_record)
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

        form.addRow("图片路径", self.image_path_label)
        form.addRow("姓名", self.name_edit)
        form.addRow("在职天数", self.days_edit)
        form.addRow("主文案", self.headline_edit)
        form.addRow("副文案", self.subheadline_edit)
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
        self.preview_image = QLabel("导入记录后显示预览")
        self.preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image.setMinimumWidth(360)
        self.preview_image.setStyleSheet("background:#f4f4f4;border:1px solid #d8d8d8;")
        export_button = QPushButton("批量导出")
        export_button.clicked.connect(self.export_all)
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_image, stretch=1)
        preview_layout.addWidget(export_button)
        splitter.addWidget(preview_panel)
        splitter.setSizes([280, 400, 500])

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

    def import_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择人物图片文件夹")
        if not folder:
            return
        paths = sorted(Path(folder).iterdir())
        imported = []
        start_index = len(self.records)
        for path in paths:
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            name = infer_name_from_path(path)
            index = start_index + len(imported)
            record = BadgeRecord(
                image_path=str(path),
                name=name,
                days="1193",
                headline=build_headline("1193"),
                subheadline=DEFAULT_SUBHEADLINE,
                output_name=f"{index + 1:02d} {name}-离职厂牌-.png",
            )
            imported.append(record)

        if not imported:
            QMessageBox.information(self, "未找到图片", "所选目录中没有可用的 PNG/JPG/WEBP 图片。")
            return

        self.records.extend(imported)
        self._refresh_list()
        self.list_widget.setCurrentRow(start_index)

    def _refresh_list(self) -> None:
        self.list_widget.clear()
        for index, record in enumerate(self.records):
            title = f"{index + 1:02d} | {record.name} | {Path(record.image_path).name}"
            item = QListWidgetItem(title)
            self.list_widget.addItem(item)

    def _on_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self.records):
            self._clear_form()
            return
        self._loading_form = True
        record = self.records[row]
        self.image_path_label.setText(record.image_path)
        self.name_edit.setText(record.name)
        self.days_edit.setText(record.days)
        self.headline_edit.setText(record.headline)
        self.subheadline_edit.setText(record.subheadline)
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
        self.days_edit.clear()
        self.headline_edit.clear()
        self.subheadline_edit.setText(DEFAULT_SUBHEADLINE)
        self.output_edit.clear()
        self.scale_spin.setValue(1.0)
        self.x_spin.setValue(0)
        self.y_spin.setValue(0)
        self._loading_form = False
        self.preview_image.setText("导入记录后显示预览")
        self.preview_image.setPixmap(QPixmap())

    def _current_record(self) -> BadgeRecord | None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.records):
            return None
        return self.records[row]

    def _sync_form_to_record(self) -> None:
        if self._loading_form:
            return
        record = self._current_record()
        if not record:
            return
        record.name = self.name_edit.text().strip()
        record.days = self.days_edit.text().strip()
        record.headline = self.headline_edit.text().strip()
        record.subheadline = self.subheadline_edit.text().strip()
        record.output_name = self.output_edit.text().strip()
        record.scale_adjust = self.scale_spin.value()
        record.x_offset = self.x_spin.value()
        record.y_offset = self.y_spin.value()
        self._refresh_list()
        self.list_widget.setCurrentRow(self.records.index(record))
        self.refresh_preview()

    def _on_days_changed(self) -> None:
        if self._loading_form:
            return
        record = self._current_record()
        if not record:
            return
        record.days = self.days_edit.text().strip()
        auto_headline = build_headline(record.days)
        if not self.headline_edit.text().strip() or self.headline_edit.text().startswith("和奥马一起走过"):
            self._loading_form = True
            self.headline_edit.setText(auto_headline)
            self._loading_form = False
        self._sync_form_to_record()

    def refresh_preview(self) -> None:
        record = self._current_record()
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

    def remove_current_record(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            return
        self.records.pop(row)
        self._refresh_list()
        if self.records:
            self.list_widget.setCurrentRow(min(row, len(self.records) - 1))
        else:
            self._clear_form()

    def export_all(self) -> None:
        if not self.records:
            QMessageBox.information(self, "没有记录", "请先导入图片。")
            return
        output_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not output_dir:
            return
        failures = []
        for record in self.records:
            try:
                export_badge(record, output_dir)
            except Exception as exc:
                failures.append(f"{record.output_name}: {exc}")

        if failures:
            QMessageBox.warning(self, "部分导出失败", "\n".join(failures))
        else:
            QMessageBox.information(self, "导出完成", f"已导出 {len(self.records)} 张图片。")

    def save_project_file(self, save_as: bool = False) -> None:
        if not self.records:
            QMessageBox.information(self, "没有记录", "请先导入图片或打开工程。")
            return
        if save_as or self.current_project_path is None:
            selected, _ = QFileDialog.getSaveFileName(self, "保存工程", "", "JSON Files (*.json)")
            if not selected:
                return
            self.current_project_path = Path(selected)
        save_project(self.current_project_path, self.records)
        QMessageBox.information(self, "保存成功", f"工程已保存到：\n{self.current_project_path}")

    def open_project(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "打开工程", "", "JSON Files (*.json)")
        if not selected:
            return
        self.records = load_project(selected)
        self.current_project_path = Path(selected)
        self._refresh_list()
        if self.records:
            self.list_widget.setCurrentRow(0)
        else:
            self._clear_form()


def run_gui() -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()

