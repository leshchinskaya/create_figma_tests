import json
import os
import config


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config_artifacts.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Ошибка: Конфигурационный файл '{config_path}' не найден.")
        return
    except json.JSONDecodeError:
        print(f"❌ Ошибка: Некорректный формат JSON в файле '{config_path}'.")
        return
    except Exception as e:
        print(f"❌ Ошибка при чтении конфигурационного файла '{config_path}': {e}")
        return

    prompt_template_path = config.get('prompt_template_path')
    output_prompt_path = config.get('output_prompt_path')
    artifacts_paths = config.get('artifacts', {})
    placeholders = config.get('placeholders', {})

    if not prompt_template_path:
        print("❌ Ошибка: 'prompt_template_path' не указан в конфигурации.")
        return
    if not output_prompt_path:
        print("❌ Ошибка: 'output_prompt_path' не указан в конфигурации.")
        return

    if prompt_template_path and not os.path.isabs(prompt_template_path):
        prompt_template_path = os.path.join(script_dir, prompt_template_path)
    if output_prompt_path and not os.path.isabs(output_prompt_path):
        output_prompt_path = os.path.join(script_dir, output_prompt_path)

    try:
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл шаблона '{prompt_template_path}' не найден.")
        return
    except Exception as e:
        print(f"❌ Ошибка при чтении файла шаблона '{prompt_template_path}': {e}")
        return

    for artifact_key, artifact_path in artifacts_paths.items():
        placeholder = placeholders.get(artifact_key)
        if not placeholder:
            print(
                f"⚠️ Предупреждение: Плейсхолдер для артефакта '{artifact_key}' не найден в конфигурации. Пропуск."
            )
            continue
        if artifact_path and not os.path.isabs(artifact_path):
            artifact_path = os.path.join(script_dir, artifact_path)
        try:
            with open(artifact_path, 'r', encoding='utf-8') as f:
                artifact_content = f.read()
            prompt_content = prompt_content.replace(placeholder, artifact_content)
        except FileNotFoundError:
            print(
                f"❌ Ошибка: Файл артефакта '{artifact_path}' (для ключа '{artifact_key}') не найден. Выполнение прервано."
            )
            return
        except Exception as e:
            print(f"❌ Ошибка при чтении файла артефакта '{artifact_path}': {e}")
            return

    swagger_url = getattr(config, 'SWAGGER_URL', '')
    prompt_content = prompt_content.replace('{{SWAGGER_URL}}', swagger_url)

    try:
        with open(output_prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        print(f"✅ Файл '{output_prompt_path}' успешно сгенерирован.")
    except Exception as e:
        print(f"❌ Ошибка при записи в файл '{output_prompt_path}': {e}")


if __name__ == '__main__':
    main()
