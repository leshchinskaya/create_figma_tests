import sys
import os
import pathlib
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QComboBox, QPushButton, QTextEdit, QLabel, QApplication)
from PyQt5.QtCore import Qt, QCoreApplication, QProcess # QProcess needed for ExitStatus enum
from PyQt5.QtGui import QTextCursor # Added import
from .script_executor import ScriptExecutor # Relative import

class AppWindow(QMainWindow):
    def __init__(self, project_root: pathlib.Path, parent=None):
        super().__init__(parent)
        self.project_root = project_root
        self.script_executor = ScriptExecutor(self)

        # Define scripts relative to project_root
        self.scripts_to_run = [
            {
                "name": "Генерация тест-кейсов из Figma",
                "path": "./send_figma_tests_all_tests.py",
                "cwd": "." # Relative to project root, so project_root itself
            },
            {
                "name": "Сгенерировать промпт для создания тестов",
                "path": "./create_final_tests/create_final_promt.py",
                "cwd": "." # Relative to project root
            },
            {
                "name": "Отправка финальных тест-кейсов в Jira",
                "path": "./send_final_tests.py",
                "cwd": "." # Relative to project root
            },
        ]

        self.setWindowTitle("Generator of tests from Figma")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Script selection
        self.script_selector_label = QLabel("Выберите скрипт:")
        self.layout.addWidget(self.script_selector_label)

        self.script_selector = QComboBox()
        for i, script_info in enumerate(self.scripts_to_run):
            self.script_selector.addItem(script_info["name"], userData=i)
        self.layout.addWidget(self.script_selector)

        # Run button
        self.run_button = QPushButton("Запустить скрипт")
        self.run_button.clicked.connect(self.start_selected_script)
        self.layout.addWidget(self.run_button)

        # Status label
        self.status_label = QLabel("Статус: Готов")
        self.layout.addWidget(self.status_label)

        # Output area
        self.output_area_label = QLabel("Вывод скрипта:")
        self.layout.addWidget(self.output_area_label)
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFontFamily("Courier") # Monospaced font for logs
        self.layout.addWidget(self.output_area)

        # Connect executor signals
        self.script_executor.outputReady.connect(self.append_output)
        self.script_executor.errorReady.connect(self.append_error)
        self.script_executor.started.connect(self.on_script_started)
        self.script_executor.finished.connect(self.on_script_finished)

    def start_selected_script(self):
        selected_index = self.script_selector.currentData()
        if selected_index is None or selected_index >= len(self.scripts_to_run):
            self.status_label.setText("Статус: Ошибка - неверный выбор скрипта")
            return

        script_info = self.scripts_to_run[selected_index]
        
        # Paths from config are relative to project_root
        relative_script_file_str = script_info["path"]
        relative_script_cwd_str = script_info["cwd"]

        # Resolve them against project_root to get absolute paths
        # actual_script_executable is the full path to the .py file to be executed
        actual_script_executable = (self.project_root / relative_script_file_str).resolve()
        # actual_working_directory is the CWD from which the script will be run
        actual_working_directory = (self.project_root / relative_script_cwd_str).resolve()

        if not actual_script_executable.exists():
            # Use the resolved path in the error message for clarity
            self.append_output(f"Ошибка: Файл скрипта не найден: {actual_script_executable}\n")
            self.status_label.setText(f"Статус: Ошибка - файл скрипта не найден")
            return

        self.output_area.clear()
        self.append_output(f"Запуск скрипта: {script_info['name']}...\n")
        # Log the resolved, absolute paths
        self.append_output(f"Путь: {actual_script_executable}\n")
        self.append_output(f"Рабочая директория: {actual_working_directory}\n\n")
        
        self.run_button.setEnabled(False)
        self.status_label.setText("Статус: Запускается...")
        
        # Pass resolved paths as strings to the executor
        self.script_executor.run_script(str(actual_script_executable), str(actual_working_directory))

    def append_output(self, text: str):
        self.output_area.moveCursor(QTextCursor.End)
        self.output_area.insertPlainText(text)
        self.output_area.moveCursor(QTextCursor.End)

    def append_error(self, text: str):
        self.append_output(text) # For now, stderr is mixed with stdout. Can be styled differently.

    def on_script_started(self):
        self.status_label.setText("Статус: Выполняется...")
        self.run_button.setEnabled(False)

    def on_script_finished(self, exit_code: int, exit_status_enum: QProcess.ExitStatus):
        status_text = "Статус: "
        if exit_status_enum == QProcess.NormalExit:
            status_text += f"Завершено (код: {exit_code})"
        else: # CrashExit
            status_text += f"Завершено с ошибкой (код: {exit_code})"
        
        self.status_label.setText(status_text)
        self.append_output(f"\n--- Скрипт завершен ---\n{status_text}\n")
        self.run_button.setEnabled(True)

    def closeEvent(self, event):
        if self.script_executor and self.script_executor.process and \
           self.script_executor.process.state() == QProcess.Running:
            self.script_executor.stop_script()
        super().closeEvent(event) 