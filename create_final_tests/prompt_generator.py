import json
import os
import platform
import subprocess
from pathlib import Path

import config as config_module


def generate_prompt_from_config(
    config_path: str, output_path: str, json_path: str | None = None
) -> bool:
    """Generate a prompt file based on a JSON config of artifacts."""
    script_dir = Path(__file__).resolve().parent
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Ошибка: Конфигурационный файл '{config_path}' не найден.")
        return False
    except json.JSONDecodeError:
        print(f"❌ Ошибка: Некорректный формат JSON в файле '{config_path}'.")
        return False
    except Exception as e:
        print(f"❌ Ошибка при чтении конфигурационного файла '{config_path}': {e}")
        return False

    prompt_template_path = config_data.get('prompt_template_path')
    artifacts_paths = config_data.get('artifacts', {})
    placeholders = config_data.get('placeholders', {})

    swagger_override = getattr(config_module, 'SWAGGER_LOCAL_PATH', '').strip()
    if swagger_override:
        swagger_path = Path(swagger_override)
        config_dir = Path(config_module.__file__).resolve().parent
        if not swagger_path.is_absolute():
            swagger_path = config_dir / swagger_path
        artifacts_paths['swagger'] = str(swagger_path)

    if not prompt_template_path:
        print("❌ Ошибка: 'prompt_template_path' не указан в конфигурации.")
        return False

    path_obj = Path(prompt_template_path)
    if not path_obj.is_absolute():
        path_obj = script_dir / path_obj
    prompt_template_path = path_obj

    output_prompt_path = Path(output_path)
    if not output_prompt_path.is_absolute():
        output_prompt_path = script_dir / output_prompt_path

    try:
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл шаблона '{prompt_template_path}' не найден.")
        return False
    except Exception as e:
        print(f"❌ Ошибка при чтении файла шаблона '{prompt_template_path}': {e}")
        return False

    for artifact_key, artifact_path in artifacts_paths.items():
        placeholder = placeholders.get(artifact_key)
        if not placeholder:
            print(
                f"⚠️ Предупреждение: Плейсхолдер для артефакта '{artifact_key}' не найден в конфигурации. Пропуск."
            )
            continue
        if artifact_path:
            path_obj = Path(artifact_path)
            if not path_obj.is_absolute():
                path_obj = script_dir / path_obj
            artifact_path = path_obj
        try:
            with open(artifact_path, 'r', encoding='utf-8') as f:
                artifact_content = f.read()
            prompt_content = prompt_content.replace(placeholder, artifact_content)
        except FileNotFoundError:
            print(
                f"❌ Ошибка: Файл артефакта '{artifact_path}' (для ключа '{artifact_key}') не найден. Выполнение прервано."
            )
            return False
        except Exception as e:
            print(f"❌ Ошибка при чтении файла артефакта '{artifact_path}': {e}")
            return False

    swagger_url = getattr(config_module, 'SWAGGER_URL', '')
    prompt_content = prompt_content.replace('{{SWAGGER_URL}}', swagger_url)

    try:
        with open(output_prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        print(f"✅ Файл '{output_prompt_path}' успешно сгенерирован.")

        if getattr(config_module, "AUTOLAUNCH_FILES", False):
            def _open(path: Path):
                try:
                    if platform.system() == "Darwin":
                        subprocess.Popen(["open", str(path)])
                    elif platform.system() == "Windows":
                        os.startfile(path)
                    else:
                        subprocess.Popen(["xdg-open", str(path)])
                except Exception as open_err:
                    print(f"⚠️ Не удалось открыть файл {path}: {open_err}")

            _open(output_prompt_path)
            if json_path:
                json_target = Path(json_path)
                if not json_target.is_absolute():
                    json_target = output_prompt_path.parent / json_target
                if not json_target.exists():
                    try:
                        json_target.touch()
                    except Exception as touch_err:
                        print(f"⚠️ Не удалось создать файл {json_target}: {touch_err}")
                _open(json_target)

        return True
    except Exception as e:
        print(f"❌ Ошибка при записи в файл '{output_prompt_path}': {e}")
        return False


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Generate a final prompt from a template and artifacts.")
    parser.add_argument("--config", required=True, help="Path to the JSON config file for artifacts.")
    parser.add_argument("--output", required=True, help="Path to the output prompt file.")
    parser.add_argument("--json", help="Path to the JSON file that will store AI response.")
    args = parser.parse_args()

    if generate_prompt_from_config(args.config, args.output, args.json):
        print(f"✅ Prompt successfully generated at: {args.output}")
    else:
        print(f"❌ Failed to generate prompt.")
        exit(1)
