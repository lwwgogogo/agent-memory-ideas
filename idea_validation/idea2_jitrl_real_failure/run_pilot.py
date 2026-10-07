"""Execute the frozen two-episode technical pilot."""
from runtime_runner import execute_run

if __name__ == "__main__":
    summary = execute_run("pilot", episodes=2, max_calls=20)
    print(summary)
