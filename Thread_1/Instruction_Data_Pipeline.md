# HƯỚNG DẪN CHẠY DATA PIPELINE - PHÁT HIỆN GREENWASHING

Quy trình đã được tối ưu hóa chuẩn xác theo mô hình Medallion Data Architecture (Bronze -> Silver -> Gold -> Scoring -> Analysis).

Dưới đây là thứ tự chạy các file từ A-Z để xử lý cho 1 vòng (ví dụ: Ngân hàng BIDV năm 2023):

### BƯỚC 1: THU THẬP LINK TIN TỨC (BRONZE)

📄 **File chạy:** `craw_with_gnews.ipynb`

* **Mục đích:** Tìm link tất cả các bài báo từ các trang do bạn cấu hình (như baochinhphu.vn) có tên ngân hàng "BIDV" trong Tiêu đề.
* **Đầu vào (Cấu hình):** Chỉnh biến `YEAR = 2023`, `BANKS = {"BIDV": ["BIDV", "Ngân hàng BIDV"...]}`.
* **Đầu ra:** Folder `data/2023/BIDV/bronze/` chứa file Excel và Word. File quan trọng nhất là file có đuôi `_filter.xlsx`.

### BƯỚC 2: CÀO NỘI DUNG TOÀN VĂN (SILVER - 1)

📄 **File chạy:** `crawl_contents_from_filter_excels.py`

* **Mục đích:** Đọc file `_filter.xlsx` phía trên để vào trong tận bài báo gốc copy chữ mang về.
* **Đầu ra:** Data sẽ nằm gọn tại `data/2023/BIDV/silver/1/{Tên-File}.json`. Cấu trúc JSON có lưu đẩy đủ thông tin (Link, Nội dung báo).

### BƯỚC 3: LỌC BỎ BÀI TRÙNG LẶP (SILVER - 2)

📄 **File chạy:** `silver_dedupe_near_duplicates.ipynb`

* **Mục đích:** Xóa những bài báo bị các trang copy/paste của nhau (kiểm tra độ giống nhau > 90%).
* **Đầu ra:** Dữ liệu tinh gọn được push sang `data/2023/BIDV/silver/2/{Tên-File}.json`.

### BƯỚC 4: RÚT TIN ESG VÀ CHẤM VỚI AI (SILVER - 3)

📄 **File chạy:** `ESG_check_with_LLMs.ipynb`

* **Mục đích:** Sử dụng OpenRouter LLM để đọc, lọc xem bài báo có liên quan thiết thực đến Môi trường & Xã hội không, loại bỏ các bài báo rác (ví dụ: cướp ngân hàng). Và trả ra trường `content` gốc để dùng cho chấm Greenwashing Index.
* **Đầu ra:** File làm sạch lưu tại `data/2023/BIDV/silver/3/{Tên-File}.json`.

### BƯỚC 5: TIỀN XỬ LÝ NLP TIẾNG VIỆT (GOLD)

📄 **File chạy:** `gold_text_preprocessing.ipynb`

* **Mục đích:** Áp dụng phương pháp Tokenize/Word Segment của bài báo khoa học. Xóa dấu câu, viết thường, loại bỏ Stopwords (Từ vô nghĩa) bằng `pyvi` giúp máy hiểu được cấu trúc ngôn ngữ Việt (ví dụ: gắn chữ `môi` và `trường` lại với nhau thành `môi_trường`).
* **Đầu ra:** Folder dán nhãn chuẩn chỉ dùng để máy học tên là `data/2023/BIDV/gold/{Tên-File}.json` - đã ngậm biến `preprocessed_content`.

### BƯỚC 6: TÍNH ĐIỂM CHỈ SỐ GSI - CHẤM TIN TỨC VÀ BÁO CÁO NH

📄 **File chạy:** `sentiment_comparative_scoring.ipynb`

* **Mục đích:**
  1. *Cho Tin tức:* Nạp các file Gold, đếm số từ có trong `ESG_Dictionary/ESG.xlsx` (nhân theo Trọng số tính từ -3 đến +3) -> Tính Comparative Score và nhét vào `scoring/`.
  2. *Cho Báo cáo:* Nạp PDF báo cáo (bằng cách trỏ trực tiếp biến `MANUAL_PDF_PATH = r"D:\...\Bao_cao_BIDV.pdf"` trong ô Cell thứ 7) để tính điểm.
* **Đầu ra:** Data `scored_*.json` của NH và Tin Tức sẽ cùng hội ngộ tại `data/2023/BIDV/scoring/`.

### BƯỚC 7: XUẤT CỜ ĐỎ (GAP ANALYSIS / DISSONANCE)

📄 **File chạy:** `consistency_assessment_pearson.ipynb`

* **Mục đích:** Bước cuối cùng để máy tính tự động đối chiếu điểm trung bình Báo cáo (X) với điểm trung bình Tin Tức (Y).
* **Đầu vào (Cấu hình):** Bạn nhập `BANK_NAME = "BIDV"`, máy sẽ tự gom file json trong chuỗi.
* **Đầu ra:** Hệ thống in ra màn hình Delta $\Delta_{Gap}$. Nếu mức chênh lệch quá lớn (Dương mạnh), máy giương cờ cảnh báo (Greenwashing Detected). Nếu lệch ít: An toàn.
