import time
from app import app
from models import db, Comment
from crud import get_comments_by_task

def benchmark():
    with app.app_context():
        start = time.perf_counter()
        for _ in range(100):
            comments, total = get_comments_by_task(1, page=1, per_page=20)
        end = time.perf_counter()
        print(f"100 вызовов get_comments_by_task: {end - start:.4f} сек")

if __name__ == '__main__':
    benchmark()