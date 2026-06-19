"""
Бенчмарк для измерения времени отклика API комментариев.
"""
import time
import requests
import sys

BASE_URL = 'http://127.0.0.1:5000/api'

def measure_get_comments(task_id=1, iterations=100):
    """Измеряет среднее время GET /comments/ для заданной задачи."""
    # Проверка доступности сервера
    try:
        requests.get(f'{BASE_URL}/comments/?task_id={task_id}', timeout=2)
    except requests.ConnectionError:
        print('❌ Сервер Flask не запущен! Запустите python app.py в отдельном терминале.')
        sys.exit(1)

    url = f'{BASE_URL}/comments/?task_id={task_id}'
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        resp = requests.get(url)
        end = time.perf_counter()
        if resp.status_code == 200:
            times.append(end - start)
        else:
            print(f'Ошибка: {resp.status_code}')
    avg = sum(times) / len(times) if times else 0
    print(f'✅ GET /comments/ среднее время за {iterations} запросов: {avg:.4f} сек')
    return avg

if __name__ == '__main__':
    measure_get_comments()