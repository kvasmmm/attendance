import os 
def remove_file_if_exists(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except PermissionError:
            print(f"Could not delete {file_path} due to permission issues.")
            pass # Игнорируем блокировки винды
[remove_file_if_exists(dbg_file) for dbg_file in os.listdir() if dbg_file.endswith("_debug.txt")]