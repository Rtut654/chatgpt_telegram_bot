import multiprocessing

from bot import run_bot
from src_bot.services.payment.client import run_client

if __name__ == '__main__':
    # Создание процессов для Telegram бота и клиента платежной системы
    telegram_process = multiprocessing.Process(target=run_bot)
    flask_process = multiprocessing.Process(target=run_client)

    # Запуск процессов
    telegram_process.start()
    flask_process.start()

    # Ожидание завершения процессов
    telegram_process.join()
    flask_process.join()
