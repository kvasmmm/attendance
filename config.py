import socket
import os
from logger import logger

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Не обязательно должно быть доступно, просто ищет правильный интерфейс
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_subnet(ip):
    """Возвращает первые три октета IP (например, '192.168.1.')"""
    if ip == '127.0.0.1':
        return '127.0.0.'
    parts = ip.split('.')
    if len(parts) == 4:
        return ".".join(parts[:3]) + "."
    return None

# Глобальные настройки
HOST_IP = get_local_ip()
ALLOWED_SUBNET = get_subnet(HOST_IP)
# Для отладки или тестов можно добавить список исключений
TRUSTED_IPS = ["127.0.0.1", "testclient"]

logger.info(f"System Network Config: Host IP={HOST_IP}, Allowed Subnet={ALLOWED_SUBNET}*")
