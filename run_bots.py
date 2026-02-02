import subprocess
import logging
import time
import sys
import os

# Настраиваем логирование, чтобы видеть статусы запуска
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_bot(command):
    """Функция для запуска одного бота и логирования результата."""
    try:
        # Используем Popen для запуска бота в отдельном процессе
        process = subprocess.Popen(command, shell=False)
        logging.info(f"Команда '{' '.join(command)}' успешно запущена. PID процесса: {process.pid}")
        return process
    except FileNotFoundError:
        logging.error(f"Ошибка: Не удалось найти файл для команды '{' '.join(command)}'. Убедитесь, что путь правильный и папка '{os.path.dirname(command[1])}' существует.")
        return None
    except Exception as e:
        logging.error(f"Не удалось запустить процесс '{' '.join(command)}': {e}")
        return None

if __name__ == '__main__':
    logging.info("Инициализация запуска ботов проекта twork...")
    
    # --- ОБНОВЛЕНИЕ ---
    # Добавлен третий бот 'tdrainer stars/run.py'
    bots_to_start = [
        [sys.executable, 'tworker/run.py'],
        [sys.executable, 'tdrainer/run.py'],
        [sys.executable, 'tdrainer stars/run.py']
    ]
    
    processes = []
    
    # Запускаем ботов по очереди
    for bot_cmd in bots_to_start:
        proc = run_bot(bot_cmd)
        if proc:
            processes.append(proc)
        time.sleep(3) # Небольшая пауза между запусками для стабильности

    if processes:
        logging.info("Все боты запущены. Главный скрипт продолжает работу для их поддержки.")
        logging.info("Для остановки всех ботов нажмите Ctrl+C.")
    else:
        logging.warning("Ни один бот не был запущен. Проверьте ошибки выше.")

    try:
        # Этот цикл держит главный скрипт активным.
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Получен сигнал на остановку (Ctrl+C). Завершение работы ботов...")
        for proc in processes:
            proc.terminate() # Отправляем сигнал на завершение каждому процессу
        logging.info("Все дочерние процессы остановлены.")