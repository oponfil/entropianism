#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для конвертации текстового учебника в PDF через HTML.
Использует браузерный рендеринг (как convertio.co) для правильного отображения эмодзи.

Использование:
    python txt_to_pdf.py

Требования:
    - Python 3.6+
    - playwright (установить через: pip install playwright)
    - playwright install chromium (запустить один раз для установки браузера)

Скрипт автоматически конвертирует файл docs/ru/Entropianism_Textbook.txt
в docs/ru/Entropianism_Textbook.pdf
"""

import sys
from pathlib import Path
import html
from playwright.sync_api import sync_playwright

def create_html_from_text(input_file, output_html):
    """Создает HTML файл из текстового файла."""
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    html_content = []
    html_content.append("""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Учебник Энтропианства</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: black;
            text-align: left;
        }
        p {
            margin: 0.3cm 0;
            white-space: pre-wrap;
        }
        .empty-line {
            height: 0.3cm;
        }
    </style>
</head>
<body>
""")
    
    current_paragraph = []
    
    for line in lines:
        # Сохраняем оригинальную строку с отступами
        line_original = line.rstrip('\n\r')
        
        # Пустая строка завершает текущий абзац
        if not line_original.strip():
            if current_paragraph:
                # Объединяем строки абзаца, сохраняя переносы и отступы
                para_text = '\n'.join(current_paragraph)
                if para_text.strip():
                    escaped = html.escape(para_text)
                    html_content.append(f"    <p>{escaped}</p>\n")
                current_paragraph = []
            html_content.append('    <div class="empty-line"></div>\n')
        else:
            current_paragraph.append(line_original)
    
    # Добавляем последний абзац
    if current_paragraph:
        para_text = '\n'.join(current_paragraph)
        if para_text.strip():
            escaped = html.escape(para_text)
            html_content.append(f"    <p>{escaped}</p>\n")
    
    html_content.append("""</body>
</html>
""")
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(''.join(html_content))
    
    print(f"HTML file created: {output_html}")


def convert_html_to_pdf_playwright(html_file, pdf_file):
    """Конвертирует HTML в PDF используя Playwright (браузерный рендеринг)."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Загружаем HTML файл
            html_path = Path(html_file).absolute().as_uri()
            page.goto(html_path)
            
            # Генерируем PDF
            page.pdf(
                path=str(pdf_file),
                format='A4',
                margin={
                    'top': '2cm',
                    'right': '2cm',
                    'bottom': '2cm',
                    'left': '2cm'
                },
                print_background=True
            )
            
            browser.close()
        
        print(f"PDF created successfully using Playwright: {pdf_file}")
        return True
    except ImportError:
        print("Playwright not installed. Install with: pip install playwright")
        print("Then run: playwright install chromium")
        return False
    except Exception as e:
        print(f"Error with Playwright: {e}")
        return False




def main():
    """Главная функция."""
    input_file = Path('docs/ru/Entropianism_Textbook.txt')
    html_file = Path('docs/ru/Entropianism_Textbook_temp.html')
    pdf_file = Path('docs/ru/Entropianism_Textbook.pdf')
    
    if not input_file.exists():
        print(f"Error: File {input_file} not found!")
        sys.exit(1)
    
    # Создаем HTML файл
    print("Creating HTML file...")
    create_html_from_text(input_file, html_file)
    
    # Конвертируем HTML в PDF используя Playwright
    print("\nConverting HTML to PDF...")
    
    if convert_html_to_pdf_playwright(html_file, pdf_file):
        html_file.unlink()  # Удаляем временный HTML файл
    else:
        print("\nError: Could not convert HTML to PDF.")
        print("Please install playwright: pip install playwright")
        print("Then run: playwright install chromium")
        sys.exit(1)


if __name__ == '__main__':
    main()

