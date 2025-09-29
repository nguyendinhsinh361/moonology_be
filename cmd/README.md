# PDF to Text Converter

Bộ công cụ chuyển đổi PDF sang text với khả năng xử lý ảnh bằng OCR.

## Cài đặt

1. Cài đặt các dependencies:
```bash
pip install -r requirements.txt
```

2. Cài đặt Tesseract OCR (cho khả năng đọc text từ ảnh):

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
- Tải từ: https://github.com/UB-Mannheim/tesseract/wiki
- Thêm vào PATH

## Sử dụng

### 1. Script đơn giản (không có OCR)

```bash
python simple_pdf_converter.py input.pdf output.txt
```

### 2. Script đầy đủ tính năng

**Chuyển đổi sang text:**
```bash
python pdf_to_text.py input.pdf -o output.txt
```

**Chuyển đổi sang JSON:**
```bash
python pdf_to_text.py input.pdf --format json -o output.json
```

**Bỏ qua xử lý ảnh:**
```bash
python pdf_to_text.py input.pdf --no-images -o output.txt
```

**Chỉ định đường dẫn Tesseract:**
```bash
python pdf_to_text.py input.pdf --tesseract-path /usr/local/bin/tesseract -o output.txt
```

## Các tùy chọn

- `input_pdf`: Đường dẫn đến file PDF đầu vào
- `-o, --output`: Đường dẫn file đầu ra (tùy chọn)
- `--format`: Định dạng đầu ra (`text` hoặc `json`)
- `--no-images`: Bỏ qua việc trích xuất text từ ảnh
- `--tesseract-path`: Đường dẫn đến Tesseract executable

## Ví dụ sử dụng với file PDF của bạn

```bash
# Chuyển đổi file PDF Moonology sang text
python pdf_to_text.py ../source/pdf/moonology-oracle-cardspdf_compressed.pdf -o moonology_text.txt

# Chuyển đổi sang JSON với thông tin chi tiết
python pdf_to_text.py ../source/pdf/moonology-oracle-cardspdf_compressed.pdf --format json -o moonology_data.json
```

## Lưu ý

- Script đầy đủ tính năng yêu cầu Tesseract OCR để xử lý ảnh
- Script đơn giản chỉ trích xuất text từ PDF, không xử lý ảnh
- Định dạng JSON cung cấp thông tin chi tiết hơn về cấu trúc PDF
