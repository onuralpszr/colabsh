import os
import platform

import psutil


def get_colab_info() -> None:
    print("=== System Info ===")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python Version: {platform.python_version()}")

    print("\n=== CPU Info ===")
    # Getting CPU model name via shell command for precision in Colab
    cpu_model = os.popen("lscpu | grep 'Model name'").read().strip()
    print(f"Model: {cpu_model.split(':')[-1].strip() if cpu_model else 'N/A'}")
    print(f"Physical Cores: {psutil.cpu_count(logical=False)}")
    print(f"Total Threads: {psutil.cpu_count(logical=True)}")

    print("\n=== Memory Info ===")
    mem = psutil.virtual_memory()
    print(f"Total RAM: {mem.total / (1024**3):.2f} GB")
    print(f"Available RAM: {mem.available / (1024**3):.2f} GB")

    # Check for GPU (NVIDIA-specific)
    print("\n=== GPU Info ===")
    gpu_info = os.popen("nvidia-smi --query-gpu=name --format=csv,noheader").read().strip()
    if gpu_info:
        print(f"GPU Model: {gpu_info}")
    else:
        print("No GPU detected. (Go to Runtime > Change runtime type to enable GPU)")


get_colab_info()
