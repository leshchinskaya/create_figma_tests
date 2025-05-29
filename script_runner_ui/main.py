import sys
import pathlib
from PyQt5.QtWidgets import QApplication, QMessageBox
from .app_window import AppWindow # Relative import

def main():
    project_root = pathlib.Path(__file__).resolve().parent.parent
    
    app = QApplication(sys.argv)
    
    config_py_path = project_root / "config.py"
    if not config_py_path.exists():
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Предупреждение о конфигурации")
        msg_box.setText(f"Файл 'config.py' не найден в корне проекта ({project_root}).\n\n"
                        f"Скрипты могут не работать корректно.\n"
                        f"Пожалуйста, создайте 'config.py' из 'config_template.py' и заполните его.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
        # Application will continue, scripts might fail, which is informative.

    main_window = AppWindow(project_root=project_root)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 