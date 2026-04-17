"""
Скрипт для трансляции экрана (СЕРВЕР)
Запуск: python server.py
"""

import pyautogui
import cv2
import numpy as np
import socket
import struct
import pickle
import threading
import time
import sys
from datetime import datetime

class ScreenBroadcaster:
    def __init__(self, port=9999, quality=70, fps=20):
        """
        Инициализация транслятора
        
        Параметры:
        port - порт для подключения
        quality - качество JPEG (1-100)
        fps - кадров в секунду
        """
        self.port = port
        self.quality = quality
        self.fps = fps
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.broadcasting = False
        
    def start(self):
        """Запуск сервера и ожидание подключения"""
        try:
            # Создаем сокет
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(1)
            
            print("=" * 50)
            print("ТРАНСЛЯТОР ЭКРАНА")
            print("=" * 50)
            print(f"Сервер запущен на порту: {self.port}")
            print(f"Качество: {self.quality}")
            print(f"FPS: {self.fps}")
            print("=" * 50)
            print("Ожидание подключения зрителя...")
            print(f"IP адреса для подключения:")
            
            # Получаем IP адреса
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"  - Локальный: {local_ip}:{self.port}")
            
            # Пробуем получить внешний IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                external_ip = s.getsockname()[0]
                s.close()
                print(f"  - Внешний: {external_ip}:{self.port}")
            except:
                pass
                
            print("=" * 50)
            
            # Принимаем подключение
            self.client_socket, client_address = self.server_socket.accept()
            print(f"\n✓ Зритель подключен! Адрес: {client_address}")
            print("Начинается трансляция...")
            print("Нажмите Ctrl+C для остановки\n")
            
            self.running = True
            self.broadcasting = True
            
            # Запускаем трансляцию
            self.broadcast_screen()
            
        except KeyboardInterrupt:
            print("\n\nОстановка сервера...")
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            self.stop()
    
    def broadcast_screen(self):
        """Основной цикл трансляции экрана"""
        try:
            frame_count = 0
            start_time = time.time()
            
            while self.running and self.broadcasting:
                # Захватываем экран
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Оптимизируем размер для передачи
                screen_height, screen_width = frame.shape[:2]
                max_width = 1280  # Максимальная ширина для передачи
                if screen_width > max_width:
                    scale = max_width / screen_width
                    new_width = int(screen_width * scale)
                    new_height = int(screen_height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Сжимаем в JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
                result, encoded_frame = cv2.imencode('.jpg', frame, encode_param)
                
                # Сжимаем данные
                data = pickle.dumps(encoded_frame)
                
                # Отправляем размер данных и сами данные
                message_size = struct.pack("!L", len(data))
                self.client_socket.sendall(message_size + data)
                
                # Статистика
                frame_count += 1
                if time.time() - start_time >= 1:
                    print(f"  FPS: {frame_count}", end='\r')
                    frame_count = 0
                    start_time = time.time()
                
                # Контроль FPS
                time.sleep(1 / self.fps)
                
        except (BrokenPipeError, ConnectionResetError):
            print("\n\n❌ Зритель отключился!")
        except Exception as e:
            print(f"\nОшибка при трансляции: {e}")
        finally:
            self.broadcasting = False
    
    def stop(self):
        """Остановка трансляции"""
        self.running = False
        self.broadcasting = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("\nТрансляция остановлена")
        sys.exit(0)

def check_dependencies():
    """Проверка установленных библиотек"""
    missing = []
    
    try:
        import pyautogui
    except ImportError:
        missing.append("pyautogui")
    
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    if missing:
        print("Отсутствуют необходимые библиотеки!")
        print(f"Установите их командой: pip install {' '.join(missing)}")
        return False
    return True

if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
    
    # Настройки трансляции
    PORT = 9999          # Порт для подключения
    QUALITY = 70         # Качество (1-100)
    FPS = 20             # Кадров в секунду
    
    # Запуск транслятора
    broadcaster = ScreenBroadcaster(port=PORT, quality=QUALITY, fps=FPS)
    broadcaster.start()