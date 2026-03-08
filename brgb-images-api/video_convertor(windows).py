#!/usr/bin/env python3
"""
BRGB Video Converter - Конвертер видео файлов в формат BRGB для ComputerCraft
Адаптировано для Windows
поддерживаемые форматы .mp4, .avi, .mov, .mkv, .webm, .flv, .wmv, .m4v, .mpg, .mpeg
"""

import os
import sys
import time
import math
import struct
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import ctypes

# Палитра цветов ComputerCraft в RGB (16 цветов)
CC_PALETTE = [
    (0xF0, 0xF0, 0xF0),  # white - 0
    (0xF2, 0xB2, 0x33),  # orange - 1
    (0xE5, 0x7F, 0xD8),  # magenta - 2
    (0x99, 0xB2, 0xF2),  # lightBlue - 3
    (0xDE, 0xDE, 0x6C),  # yellow - 4
    (0x7F, 0xCC, 0x19),  # lime - 5
    (0xF2, 0xB2, 0xCC),  # pink - 6
    (0x4C, 0x4C, 0x4C),  # gray - 7
    (0x99, 0x99, 0x99),  # lightGray - 8
    (0x4C, 0x99, 0xB2),  # cyan - 9
    (0xB2, 0x66, 0xE5),  # purple - 10
    (0x33, 0x66, 0xCC),  # blue - 11
    (0x7F, 0x66, 0x4C),  # brown - 12
    (0x57, 0xA6, 0x4E),  # green - 13
    (0xCC, 0x4C, 0x4C),  # red - 14
    (0x11, 0x11, 0x11),  # black - 15
]

# Таблица для быстрого поиска ближайшего цвета (кэшированная)
COLOR_CACHE = {}

class BRGBConverter:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.temp_dir = None
        self.total_frames = 0
        self.processed_frames = 0
        # Для Windows поддержки цветного вывода
        self.use_colors = self._init_windows_colors()
        
    def _init_windows_colors(self) -> bool:
        """Инициализация цветного вывода для Windows"""
        if os.name == 'nt':
            try:
                # Включаем поддержку ANSI цветов в Windows 10+
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                return False
        return False
    
    def log(self, message: str, level: str = "INFO"):
        """Логирование сообщений с цветами для Windows"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Цвета для Windows
        colors = {
            "ERROR": "\033[91m" if self.use_colors else "",
            "SUCCESS": "\033[92m" if self.use_colors else "",
            "WARNING": "\033[93m" if self.use_colors else "",
            "INFO": "\033[94m" if self.use_colors else "",
            "DEBUG": "\033[90m" if self.use_colors else "",
        }
        reset = "\033[0m" if self.use_colors else ""
        
        if self.verbose or level != "DEBUG":
            color = colors.get(level, "")
            print(f"{color}[{timestamp}] [{level}] {message}{reset}")
    
    def check_ffmpeg(self) -> bool:
        """Проверка наличия ffmpeg в Windows"""
        # Проверяем в текущей директории и в PATH
        ffmpeg_paths = [
            "ffmpeg.exe",
            Path("ffmpeg.exe"),
            Path("bin/ffmpeg.exe"),
            Path("ffmpeg/ffmpeg.exe"),
        ]
        
        # Проверяем в PATH
        try:
            result = subprocess.run(
                ['where', 'ffmpeg'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                timeout=2
            )
            if result.returncode == 0:
                return True
        except:
            pass
        
        # Проверяем в текущей директории
        for path in ffmpeg_paths:
            if Path(path).exists():
                return True
        
        # Пробуем выполнить ffmpeg
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def download_ffmpeg_windows(self) -> bool:
        """Инструкции по установке ffmpeg на Windows"""
        self.log("ffmpeg не найден!", "ERROR")
        self.log("\nИнструкция по установке ffmpeg на Windows:", "INFO")
        self.log("1. Скачайте ffmpeg с официального сайта: https://ffmpeg.org/download.html", "INFO")
        self.log("2. Выберите версию для Windows (рекомендуется полная сборка)", "INFO")
        self.log("3. Распакуйте архив в удобное место (например, C:\\ffmpeg)", "INFO")
        self.log("4. Добавьте путь к ffmpeg в переменную PATH:", "INFO")
        self.log("   - Откройте 'Система' -> 'Дополнительные параметры системы'", "INFO")
        self.log("   - Нажмите 'Переменные среды'", "INFO")
        self.log("   - Добавьте C:\\ffmpeg\\bin в переменную Path", "INFO")
        self.log("\nИли просто поместите ffmpeg.exe в ту же папку, что и скрипт", "INFO")
        
        # Спрашиваем пользователя
        response = input("\nХотите открыть страницу загрузки ffmpeg? (y/n): ")
        if response.lower() == 'y':
            try:
                os.system('start https://ffmpeg.org/download.html')
                self.log("Страница открыта в браузере", "INFO")
            except:
                self.log("Не удалось открыть браузер. Откройте ссылку вручную.", "WARNING")
        
        return False
    
    def extract_frames(self, video_path: Path, fps: int, max_frames: Optional[int]) -> Tuple[List[Path], int, int]:
        """Извлечение кадров из видео с помощью ffmpeg (Windows адаптация)"""
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="brgb_")
        
        frames_dir = Path(self.temp_dir) / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        self.log(f"Извлечение кадров из: {video_path}", "INFO")
        
        # Получаем информацию о видео
        probe_cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-f', 'null',
            '-'
        ]
        
        try:
            probe = subprocess.run(
                probe_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            # Парсим размер и FPS из вывода ffmpeg
            width, height = 160, 100  # Значения по умолчанию
            video_fps = fps
            
            import re
            for line in probe.stderr.split('\n'):
                if 'Stream #' in line and 'Video:' in line:
                    # Ищем размер
                    match = re.search(r'(\d+)x(\d+)', line)
                    if match:
                        width = int(match.group(1))
                        height = int(match.group(2))
                    
                    # Ищем FPS
                    fps_match = re.search(r'(\d+(?:\.\d+)?)\s*fps', line)
                    if fps_match:
                        video_fps = float(fps_match.group(1))
                        self.log(f"Исходный FPS видео: {video_fps}", "DEBUG")
            
            self.log(f"Размер видео: {width}x{height}", "INFO")
            
            # Команда ffmpeg для извлечения кадров
            pattern = str(frames_dir / "frame_%08d.raw")
            
            # Создаем команду для Windows
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vf', f'fps={fps}',
                '-vframes', str(max_frames) if max_frames else '999999',
                '-f', 'image2',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'rgb24',
                pattern
            ]
            
            self.log(f"Запуск ffmpeg...", "DEBUG")
            
            # Запускаем ffmpeg
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if process.returncode != 0:
                self.log(f"Ошибка ffmpeg: {process.stderr.decode('utf-8', errors='ignore')}", "ERROR")
                return [], 0, 0
            
            # Собираем список кадров
            frames = sorted(frames_dir.glob("frame_*.raw"))
            
            self.total_frames = len(frames)
            self.log(f"Извлечено кадров: {self.total_frames}", "SUCCESS")
            
            return frames, width, height
            
        except Exception as e:
            self.log(f"Ошибка при извлечении кадров: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return [], 0, 0
    
    def find_closest_color(self, r: int, g: int, b: int) -> int:
        """Поиск ближайшего цвета в палитре (с кэшированием)"""
        cache_key = (r, g, b)
        if cache_key in COLOR_CACHE:
            return COLOR_CACHE[cache_key]
        
        best_index = 0
        best_distance = float('inf')
        
        for i, (pr, pg, pb) in enumerate(CC_PALETTE):
            distance = abs(r - pr) + abs(g - pg) + abs(b - pb)
            if distance < best_distance:
                best_distance = distance
                best_index = i
        
        COLOR_CACHE[cache_key] = best_index
        return best_index
    
    def apply_dithering(self, width: int, height: int, frame_data: bytearray) -> bytearray:
        """Применение дизеринга Флойда-Стейнберга"""
        error_buffer = [[[0.0, 0.0, 0.0] for _ in range(width)] for _ in range(height)]
        result = bytearray(width * height)
        
        for y in range(height):
            for x in range(width):
                idx = (y * width + x) * 3
                
                r = min(255, max(0, frame_data[idx] + error_buffer[y][x][0]))
                g = min(255, max(0, frame_data[idx + 1] + error_buffer[y][x][1]))
                b = min(255, max(0, frame_data[idx + 2] + error_buffer[y][x][2]))
                
                color_idx = self.find_closest_color(int(r), int(g), int(b))
                result[y * width + x] = color_idx
                
                pr, pg, pb = CC_PALETTE[color_idx]
                
                err_r = r - pr
                err_g = g - pg
                err_b = b - pb
                
                if x + 1 < width:
                    error_buffer[y][x + 1][0] += err_r * 7 / 16
                    error_buffer[y][x + 1][1] += err_g * 7 / 16
                    error_buffer[y][x + 1][2] += err_b * 7 / 16
                
                if y + 1 < height:
                    if x - 1 >= 0:
                        error_buffer[y + 1][x - 1][0] += err_r * 3 / 16
                        error_buffer[y + 1][x - 1][1] += err_g * 3 / 16
                        error_buffer[y + 1][x - 1][2] += err_b * 3 / 16
                    
                    error_buffer[y + 1][x][0] += err_r * 5 / 16
                    error_buffer[y + 1][x][1] += err_g * 5 / 16
                    error_buffer[y + 1][x][2] += err_b * 5 / 16
                    
                    if x + 1 < width:
                        error_buffer[y + 1][x + 1][0] += err_r * 1 / 16
                        error_buffer[y + 1][x + 1][1] += err_g * 1 / 16
                        error_buffer[y + 1][x + 1][2] += err_b * 1 / 16
        
        return result
    
    def process_frame(self, frame_path: Path, width: int, height: int, use_dithering: bool) -> Optional[bytearray]:
        """Обработка одного кадра"""
        try:
            with open(frame_path, 'rb') as f:
                frame_data = bytearray(f.read())
            
            expected_size = width * height * 3
            if len(frame_data) != expected_size:
                self.log(f"Неверный размер кадра: {len(frame_data)} байт (ожидалось {expected_size})", "WARNING")
                return None
            
            if use_dithering:
                processed = self.apply_dithering(width, height, frame_data)
            else:
                processed = bytearray(width * height)
                for y in range(height):
                    for x in range(width):
                        idx = (y * width + x) * 3
                        r = frame_data[idx]
                        g = frame_data[idx + 1]
                        b = frame_data[idx + 2]
                        color_idx = self.find_closest_color(r, g, b)
                        processed[y * width + x] = color_idx
            
            self.processed_frames += 1
            if self.processed_frames % 10 == 0:
                progress = (self.processed_frames / self.total_frames) * 100 if self.total_frames else 0
                self.log(f"Прогресс: {self.processed_frames}/{self.total_frames} ({progress:.1f}%)", "INFO")
            
            return processed
            
        except Exception as e:
            self.log(f"Ошибка обработки кадра {frame_path}: {e}", "ERROR")
            return None
    
    def create_brgb_video(self, frames: List[bytearray], width: int, height: int, 
                         fps: int, looped: bool, output_path: Path) -> bool:
        """Создание BRGB видео файла"""
        try:
            self.log(f"Создание BRGB видео: {output_path}", "INFO")
            
            with open(output_path, 'wb') as f:
                # Заголовок BRGB
                f.write(b'BRGB')
                
                # Ширина (2 байта, little-endian для Windows)
                f.write(struct.pack('<H', width))
                
                # Высота (2 байта, little-endian)
                f.write(struct.pack('<H', height))
                
                # Флаги и FPS
                flags = 0x01  # Видео
                if looped:
                    flags |= 0x02  # Зациклено
                
                f.write(struct.pack('<B', flags))
                f.write(struct.pack('<B', min(fps, 255)))
                
                # Кадры
                for i, frame_data in enumerate(frames):
                    if frame_data:
                        # Маркер начала кадра
                        f.write(b'\xAD')
                        
                        # Данные кадра
                        f.write(frame_data)
                
                # Маркер конца файла
                f.write(b'\xFF')
            
            # Проверяем размер файла
            file_size = output_path.stat().st_size
            
            self.log(f"Файл создан: {output_path}", "SUCCESS")
            self.log(f"Размер файла: {self._format_size(file_size)}", "INFO")
            self.log(f"Количество кадров: {len(frames)}", "INFO")
            self.log(f"Разрешение: {width}x{height}", "INFO")
            self.log(f"FPS: {fps}", "INFO")
            
            return True
            
        except Exception as e:
            self.log(f"Ошибка создания BRGB файла: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def _format_size(self, size: int) -> str:
        """Форматирование размера файла"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def cleanup(self):
        """Очистка временных файлов"""
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                # На Windows нужно быть осторожным с удалением
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.log(f"Очищена временная папка: {self.temp_dir}", "DEBUG")
            except Exception as e:
                self.log(f"Ошибка очистки временной папки: {e}", "WARNING")
    
    def convert_video(self, input_path: Path, output_path: Path, 
                     fps: int = 10, max_frames: Optional[int] = None,
                     looped: bool = False, use_dithering: bool = True,
                     max_size: Optional[int] = None) -> bool:
        """Основная функция конвертации видео"""
        start_time = time.time()
        
        try:
            self.log(f"Начало конвертации: {input_path} -> {output_path}", "INFO")
            
            # Проверяем входной файл
            if not input_path.exists():
                self.log(f"Файл не найден: {input_path}", "ERROR")
                return False
            
            # Проверяем формат файла
            supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg']
            if input_path.suffix.lower() not in supported_formats:
                self.log(f"Неподдерживаемый формат: {input_path.suffix}", "WARNING")
                self.log(f"Попытка обработать...", "INFO")
            
            # Проверяем ffmpeg
            if not self.check_ffmpeg():
                self.download_ffmpeg_windows()
                return False
            
            # Извлекаем кадры
            frames, width, height = self.extract_frames(input_path, fps, max_frames)
            if not frames:
                self.log("Не удалось извлечь кадры", "ERROR")
                return False
            
            # Применяем масштабирование если нужно
            if max_size and (width > max_size or height > max_size):
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                self.log(f"Масштабирование: {width}x{height} -> {new_width}x{new_height}", "INFO")
                width, height = new_width, new_height
                # TODO: добавить реальное масштабирование через ffmpeg
            
            # Обрабатываем кадры
            processed_frames = []
            for frame_path in frames:
                processed = self.process_frame(frame_path, width, height, use_dithering)
                if processed:
                    processed_frames.append(processed)
                
                # Обновляем прогресс
                if len(processed_frames) % 10 == 0:
                    elapsed = time.time() - start_time
                    fps_proc = len(processed_frames) / elapsed if elapsed > 0 else 0
                    self.log(f"Скорость обработки: {fps_proc:.1f} кадров/сек", "DEBUG")
            
            if not processed_frames:
                self.log("Не удалось обработать ни одного кадра", "ERROR")
                return False
            
            # Создаем BRGB видео
            if not self.create_brgb_video(processed_frames, width, height, fps, looped, output_path):
                return False
            
            # Выводим статистику
            elapsed_time = time.time() - start_time
            self.log(f"Конвертация завершена за {elapsed_time:.2f} секунд", "SUCCESS")
            
            return True
            
        except KeyboardInterrupt:
            self.log("Прервано пользователем", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"Ошибка конвертации: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.cleanup()

def main():
    import argparse
    
    # Настройка аргументов командной строки
    parser = argparse.ArgumentParser(
        description='BRGB Video Converter - Конвертер видео в формат BRGB для ComputerCraft (Windows)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования (Windows):
  python video_convertor.py video.mp4 output.brgb
  python video_convertor.py input.avi animation.brgb --fps 15 --looped
  python video_convertor.py movie.mkv result.brgb --max-frames 100 --max-size 80
  
Требуется: ffmpeg.exe (поместите в папку со скриптом или добавьте в PATH)
Скачать ffmpeg: https://ffmpeg.org/download.html
"""
    )
    
    parser.add_argument('input', help='Входной видео файл')
    parser.add_argument('output', help='Выходной BRGB файл (расширение .brgb)')
    parser.add_argument('--fps', type=int, default=10,
                       help='Кадров в секунду (по умолчанию: 10)')
    parser.add_argument('--max-frames', type=int,
                       help='Максимальное количество кадров для обработки')
    parser.add_argument('--max-size', type=int,
                       help='Максимальный размер по большей стороне (пиксели)')
    parser.add_argument('--no-dither', action='store_true',
                       help='Отключить дизеринг (простое квантование)')
    parser.add_argument('--looped', action='store_true',
                       help='Создать зацикленное видео')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Подробный вывод')
    parser.add_argument('--check-ffmpeg', action='store_true',
                       help='Проверить наличие ffmpeg и выйти')
    
    args = parser.parse_args()
    
    converter = BRGBConverter(verbose=args.verbose)
    
    if args.check_ffmpeg:
        if converter.check_ffmpeg():
            print("✅ ffmpeg найден!")
            return 0
        else:
            print("❌ ffmpeg не найден!")
            print("\nСкачайте ffmpeg с официального сайта:")
            print("https://ffmpeg.org/download.html")
            return 1
    
    # Проверяем аргументы
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not output_path.suffix.lower() == '.brgb':
        output_path = output_path.with_suffix('.brgb')
        print(f"Исправлено расширение выходного файла: {output_path}")
    
    success = converter.convert_video(
        input_path=input_path,
        output_path=output_path,
        fps=args.fps,
        max_frames=args.max_frames,
        looped=args.looped,
        use_dithering=not args.no_dither,
        max_size=args.max_size
    )
    
    if success:
        print(f"\n✅ Готово! Файл сохранен как: {output_path}")
    else:
        print(f"\n❌ Ошибка конвертации!")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
