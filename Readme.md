# HƯỚNG DẪN SỬ DỤNG
## Công nghệ sử dụng
Đảm bảo máy tính của bạn cài sẵn ngôn ngữ lập trình `python` phiên bản kiến nghị `3.12.0`. Nếu chưa cài đặt vui lòng cài đặt rồi mới tiến hành được các bước tiếp theo

## Hướng dẫn sử dụng
1. Tải mã nguồn này về máy tính 
2. Sau khi tải xong thì dùng mở dự án trên `terminal` và sau đó thực hiện kích hoạt môi trường ảo hóa của `python` `venv` bằng cách sử dụng câu lệnh
``` bash
python -m venv venv
```
Sau đó kích hoạt môi trường ảo bằng `terminal` trên Window bằng câu lệnh 
``` bash
.\venv\Scripts\activate
```
3. Sau khi kích hoạt song dùng lệnh bên dưới để cài các thư viện cần thiết
``` bash
pip install -r requirements.txt
```
4. Chuẩn hóa dữ liệu đầu vào

Copy dữ liệu người dân vào file `data.csv` nằm trong thư mục `data`

Copy dữ liệu người đi khám vào file `data_kham.csv` dữ liệu này được trích xuất trên phần mềm của y tế.

5. Chạy trương trình

Sửa đường dẫn trong code nằm trong file `loc_du_lieu.csv` khớp với file ở ngoài

Sửa cấu hình trong `code` `python` nằm trong file `loc_du_lieu.csv` để hợp với địa phương.

Tiến hành chạy trương trình bằng câu lệnh
``` bash
python main.py
```

### Kết quả nằm trong thư mục `output`

6. Tiến hành tạo giấy mời bằng

Sửa đường dẫn trong code khớp với dữ liệu cần tạo giấy mời nằm trong file `dien_giay_moi.py`

Sau khi đã sửa xong tiến hành tạo giấy mời bằng câu lệnh
``` bash
python dien_giay_moi.py
```

## Giấy mời được tạo ra nằm trong thư mục giấy mời trong thư mục gốc của dự án.

### Nếu muốn sửa giấy mời thì bạn có thể sửa tùy ý trong file `gm.docx` 

Lưu ý khi sửa xong phải sửa cấu hình trong `code` để không bị lỗi khi tạo file.

# Chúc bạn thành công

