#!/usr/bin/env python3
"""
BRGB Video Converter - Конвертер видео файлов в формат BRGB для ComputerCraft
Автономный скрипт без внешних зависимостей (кроме ffmpeg)
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
        
    def log(self, message: str, level: str = "INFO"):
        """Логирование сообщений"""
        timestamp = time.strftime("%H:%M:%S")
        if self.verbose or level != "DEBUG":
            print(f"[{timestamp}] [{level}] {message}")
    
    def check_ffmpeg(self) -> bool:
        """Проверка наличия ffmpeg в системе"""
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
    
    def install_ffmpeg_linux(self) -> bool:
        """Попытка установить ffmpeg на Linux"""
        self.log("Попытка установить ffmpeg...", "WARNING")
        
        # Определяем дистрибутив
        distro = self.get_linux_distro()
        
        try:
            if distro in ["ubuntu", "debian", "linuxmint", "pop"]:
                subprocess.run(['sudo', 'apt-get', 'update'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif distro in ["fedora", "centos", "rhel"]:
                subprocess.run(['sudo', 'dnf', 'install', '-y', 'ffmpeg'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif distro in ["arch", "manjaro"]:
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.log(f"Неизвестный дистрибутив: {distro}", "ERROR")
                return False
            
            # Проверяем установку
            return self.check_ffmpeg()
            
        except Exception as e:
            self.log(f"Ошибка установки ffmpeg: {e}", "ERROR")
            return False
    
    def get_linux_distro(self) -> str:
        """Определение дистрибутива Linux"""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                
            if 'ubuntu' in content:
                return 'ubuntu'
            elif 'debian' in content:
                return 'debian'
            elif 'linuxmint' in content or 'mint' in content:
                return 'linuxmint'
            elif 'fedora' in content:
                return 'fedora'
            elif 'centos' in content:
                return 'centos'
            elif 'arch' in content:
                return 'arch'
            elif 'manjaro' in content:
                return 'manjaro'
            elif 'pop' in content:
                return 'pop'
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def extract_frames(self, video_path: Path, fps: int, max_frames: Optional[int]) -> List[Path]:
        """Извлечение кадров из видео с помощью ffmpeg"""
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="brgb_")
        
        frames_dir = Path(self.temp_dir) / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        self.log(f"Извлечение кадров из: {video_path}", "INFO")
        
        # Команда ffmpeg для извлечения кадров в raw RGB формат
        pattern = str(frames_dir / "frame_%08d.raw")
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', f'fps={fps},scale=iw*sar:ih,setsar=1',
            '-f', 'image2pipe',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-'
        ]
        
        if max_frames:
            cmd.insert(-1, '-vframes')
            cmd.insert(-1, str(max_frames))
        
        try:
            self.log(f"Запуск ffmpeg: {' '.join(cmd)}", "DEBUG")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8  # Большой буфер для видео данных
            )
            
            # Получаем информацию о размере кадра
            probe_cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-f', 'null',
                '-'
            ]
            
            probe = subprocess.run(
                probe_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            # Парсим размер из вывода ffmpeg
            width, height = 160, 100  # Значения по умолчанию
            
            for line in probe.stderr.split('\n'):
                if 'Stream #' in line and 'Video:' in line:
                    # Ищем размер в формате 1920x1080
                    import re
                    match = re.search(r'(\d+)x(\d+)', line)
                    if match:
                        width = int(match.group(1))
                        height = int(match.group(2))
                        break
            
            self.log(f"Размер видео: {width}x{height}", "INFO")
            
            # Читаем и сохраняем кадры
            frame_size = width * height * 3  # 3 байта на пиксель (RGB)
            frame_index = 0
            frames = []
            
            self.log("Обработка кадров...", "INFO")
            
            while True:
                # Читаем raw данные кадра
                raw_data = process.stdout.read(frame_size)
                if not raw_data or len(raw_data) < frame_size:
                    break
                
                # Сохраняем raw данные
                frame_path = frames_dir / f"frame_{frame_index:08d}.raw"
                with open(frame_path, 'wb') as f:
                    f.write(raw_data)
                
                # Сохраняем метаданные
                meta_path = frames_dir / f"frame_{frame_index:08d}.meta"
                with open(meta_path, 'w') as f:
                    f.write(f"{width}\n{height}\n")
                
                frames.append(frame_path)
                frame_index += 1
                
                if frame_index % 10 == 0:
                    self.log(f"Обработано кадров: {frame_index}", "INFO")
                
                if max_frames and frame_index >= max_frames:
                    break
            
            # Завершаем процесс
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            self.total_frames = len(frames)
            self.log(f"Извлечено кадров: {self.total_frames}", "SUCCESS")
            
            return frames, width, height
            
        except Exception as e:
            self.log(f"Ошибка при извлечении кадров: {e}", "ERROR")
            return [], 0, 0
    
    def find_closest_color(self, r: int, g: int, b: int) -> int:
        """Поиск ближайшего цвета в палитре (с кэшированием)"""
        # Используем кэш для ускорения
        cache_key = (r, g, b)
        if cache_key in COLOR_CACHE:
            return COLOR_CACHE[cache_key]
        
        best_index = 0
        best_distance = float('inf')
        
        # Быстрый расчет расстояния (без sqrt для скорости)
        for i, (pr, pg, pb) in enumerate(CC_PALETTE):
            # Быстрая метрика расстояния (маньхэттен)
            distance = abs(r - pr) + abs(g - pg) + abs(b - pb)
            if distance < best_distance:
                best_distance = distance
                best_index = i
        
        COLOR_CACHE[cache_key] = best_index
        return best_index
    
    def apply_dithering(self, width: int, height: int, frame_data: bytearray) -> bytearray:
        """Применение дизеринга Флойда-Стейнберга"""
        # Создаем рабочий массив с ошибками
        error_buffer = [[[0.0, 0.0, 0.0] for _ in range(width)] for _ in range(height)]
        
        # Результирующие индексы
        result = bytearray(width * height)
        
        for y in range(height):
            for x in range(width):
                # Индекс в raw данных
                idx = (y * width + x) * 3
                
                # Текущий цвет с учетом накопленных ошибок
                r = min(255, max(0, frame_data[idx] + error_buffer[y][x][0]))
                g = min(255, max(0, frame_data[idx + 1] + error_buffer[y][x][1]))
                b = min(255, max(0, frame_data[idx + 2] + error_buffer[y][x][2]))
                
                # Находим ближайший цвет
                color_idx = self.find_closest_color(int(r), int(g), int(b))
                result[y * width + x] = color_idx
                
                # Цвет из палитры
                pr, pg, pb = CC_PALETTE[color_idx]
                
                # Ошибка квантования
                err_r = r - pr
                err_g = g - pg
                err_b = b - pb
                
                # Распространяем ошибку на соседние пиксели
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
            # Читаем raw данные
            with open(frame_path, 'rb') as f:
                frame_data = bytearray(f.read())
            
            if len(frame_data) != width * height * 3:
                self.log(f"Неверный размер кадра: {len(frame_data)} байт", "WARNING")
                return None
            
            if use_dithering:
                # Применяем дизеринг
                processed = self.apply_dithering(width, height, frame_data)
            else:
                # Простое квантование
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
                self.log(f"Обработано: {self.processed_frames}/{self.total_frames}", "INFO")
            
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
                f.write(b'BRGB')  # Сигнатура
                
                # Ширина (2 байта, big-endian)
                f.write(struct.pack('>H', width))
                
                # Высота (2 байта, big-endian)
                f.write(struct.pack('>H', height))
                
                # Флаги и FPS
                flags = 0x01  # Видео
                if looped:
                    flags |= 0x02  # Зациклено
                
                f.write(struct.pack('>B', flags))  # Флаги
                f.write(struct.pack('>B', min(fps, 255)))  # FPS
                
                # Кадры
                for i, frame_data in enumerate(frames):
                    if frame_data:
                        # Маркер начала кадра
                        f.write(b'\xAD')
                        
                        # Данные кадра
                        f.write(frame_data)
                        
                        if self.verbose and i % 10 == 0:
                            self.log(f"Запись кадра {i + 1}/{len(frames)}", "DEBUG")
                
                # Маркер конца файла
                f.write(b'\xFF')
            
            # Проверяем размер файла
            file_size = output_path.stat().st_size
            expected_size = 10 + len(frames) * (1 + width * height) + 1
            
            self.log(f"Файл создан: {output_path}", "SUCCESS")
            self.log(f"Размер файла: {file_size} байт", "INFO")
            self.log(f"Количество кадров: {len(frames)}", "INFO")
            self.log(f"Разрешение: {width}x{height}", "INFO")
            self.log(f"FPS: {fps}", "INFO")
            self.log(f"Зациклено: {'Да' if looped else 'Нет'}", "INFO")
            
            return True
            
        except Exception as e:
            self.log(f"Ошибка создания BRGB файла: {e}", "ERROR")
            return False
    def cleanup(self):
        """Очистка временных файлов"""
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
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
            supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
            if input_path.suffix.lower() not in supported_formats:
                self.log(f"Неподдерживаемый формат: {input_path.suffix}", "ERROR")
                self.log(f"Поддерживаемые форматы: {', '.join(supported_formats)}", "INFO")
                return False
            
            # Проверяем ffmpeg
            if not self.check_ffmpeg():
                self.log("ffmpeg не найден!", "ERROR")
                self.log("Установите ffmpeg:", "INFO")
                self.log("  Ubuntu/Debian/Mint: sudo apt install ffmpeg", "INFO")
                self.log("  Fedora/RHEL: sudo dnf install ffmpeg", "INFO")
                self.log("  Arch: sudo pacman -S ffmpeg", "INFO")
                return False
            
            # Извлекаем кадры
            frames, width, height = self.extract_frames(input_path, fps, max_frames)
            if not frames:
                self.log("Не удалось извлечь кадры", "ERROR")
                return False
            
            # Масштабируем если нужно
            if max_size and (width > max_size or height > max_size):
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                self.log(f"Масштабирование: {width}x{height} -> {new_width}x{new_height}", "INFO")
                width, height = new_width, new_height
            processed_frames = []
            for frame_path in frames:
                processed = self.process_frame(frame_path, width, height, use_dithering)
                if processed:
                    processed_frames.append(processed)
            
            if not processed_frames:
                self.log("Не удалось обработать ни одного кадра", "ERROR")
                return False
            
            # Создаем BRGB видео
            if not self.create_brgb_video(processed_frames, width, height, fps, looped, output_path):
                return False
            
            # Создаем Lua скрипт
            lua_script = self.create_lua_loader(output_path, fps, looped)
            
            # Выводим статистику
            elapsed_time = time.time() - start_time
            self.log(f"Конвертация завершена за {elapsed_time:.2f} секунд", "SUCCESS")
            self.log(f"Результат: {output_path}", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"Ошибка конвертации: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.cleanup()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='BRGB Video Converter - Конвертер видео в формат BRGB для ComputerCraft',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s video.mp4 output.brgb
  %(prog)s input.avi animation.brgb --fps 15 --looped
  %(prog)s movie.mkv result.brgb --max-frames 100 --max-size 80
  
Форматы: MP4, AVI, MOV, MKV, WebM, FLV, WMV
Требуется: ffmpeg (установите: sudo apt install ffmpeg)
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
            print("\nУстановите ffmpeg:")
            print("  Ubuntu/Debian/Mint: sudo apt install ffmpeg")
            print("  Fedora/RHEL: sudo dnf install ffmpeg")
            print("  Arch: sudo pacman -S ffmpeg")
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
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")
        sys.exit(1)
