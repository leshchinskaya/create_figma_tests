import sys
import os
from PyQt5.QtCore import QObject, pyqtSignal, QProcess, QProcessEnvironment

class ScriptExecutor(QObject):
    outputReady = pyqtSignal(str)
    errorReady = pyqtSignal(str) # For stderr if not merged
    started = pyqtSignal()
    finished = pyqtSignal(int, QProcess.ExitStatus) # exitCode, exitStatus

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process: QProcess | None = None

    def run_script(self, script_path: str, cwd: str):
        if self.process and self.process.state() == QProcess.Running:
            self.errorReady.emit("Ошибка: Другой скрипт уже выполняется.\n")
            return

        self.process = QProcess()
        # Default is SeparateChannels, which is what we want for distinct stdout/stderr handling
        # self.process.setProcessChannelMode(QProcess.SeparateChannels) 

        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        # Ensure the script's directory is in PYTHONPATH if it relies on local sibling modules
        # and CWD is different. However, Python automatically adds script's dir to sys.path.
        # script_dir = os.path.dirname(script_path)
        # existing_pythonpath = env.value("PYTHONPATH", "")
        # env.insert("PYTHONPATH", os.pathsep.join(filter(None, [script_dir, existing_pythonpath])))
        self.process.setProcessEnvironment(env)

        self.process.setWorkingDirectory(cwd)

        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self. _handle_stderr) # Connect if using SeparateChannels
        self.process.started.connect(self.started)
        self.process.finished.connect(self._script_finished)

        program = sys.executable
        arguments = ["-u", script_path]

        self.process.start(program, arguments)

    def _handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode(sys.stdout.encoding or 'utf-8', errors='replace')
        self.outputReady.emit(data)

    def _handle_stderr(self):
        data = self.process.readAllStandardError().data().decode(sys.stderr.encoding or 'utf-8', errors='replace')
        self.errorReady.emit(data) # Emitting to errorReady, AppWindow decides how to display

    def _script_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        self.finished.emit(exit_code, exit_status)
        self.process = None 

    def stop_script(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            # Could add self.process.kill() after a timeout if terminate() is not enough 