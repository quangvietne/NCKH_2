# HƯỚNG DẪN ỐNG DẪN DỮ LIỆU (DATA PIPELINE) & GIẢI THÍCH MÃ NGUỒN

Tài liệu này hướng dẫn chi tiết luồng chạy code và giải thích ý nghĩa của từng module trong dự án NCKH về đánh giá mức độ Greenwashing của các Ngân hàng Việt Nam.

Mô hình phương pháp luận của chúng ta bao gồm **2 Luồng (Threads) tính toán đặc trưng độc lập**, sau đó gom lại để chạy **Thuật toán Phân cụm (Clustering)**.

---

## 🟢 LUỒNG 1 (THREAD 1): ĐÁNH GIÁ SỰ LỆCH PHA (DISSONANCE GAP ANALYSIS)

**Vị trí file:** `d:\NCKH\Thread_1\consistency_assessment_pearson.ipynb`

### 1. Ý nghĩa của luồng này
Luồng 1 tập trung đo lường độ chênh lệch giữa **Báo cáo nội bộ (chủ quan)** và **Tin tức Báo chí (khách quan)**.
Nó trả lời cho câu hỏi: *"Ngân hàng có đang nói quá mức về những điều tốt đẹp của mình so với những gì dư luận đang đánh giá hay không?"*

- **X (Report Score):** Điểm cảm xúc (Sentiment Score) trung bình trích xuất từ văn bản Báo cáo phát triển bền vững.
- **Y_mean (News Score):** Điểm cảm xúc trung bình trích xuất từ tất cả các bài báo viết về ngân hàng đó.
- **Delta Gap ($\Delta_{Gap}$):** Độ lệch giữa 2 góc nhìn ($X - \bar{Y}$). Đây là mức độ "Lệch pha". $\Delta$ càng lớn, rủi ro đánh bóng tên tuổi (Greenwashing) càng cao.

### 2. Cách chạy Code
1. Mở file `consistency_assessment_pearson.ipynb`.
2. Tìm đến `Cell 2` (phần Cấu hình đường dẫn), chỉnh sửa tên ngân hàng đang muốn phân tích. 
   - Ví dụ: `BANK_NAME = "BIDV"`
3. Chạy toàn bộ Notebook (**Run All**).
4. **Kết quả (Output):** Thuật toán tự động xuất ra file Excel lưu điểm Gap Score (Ví dụ: `scoring/BIDV_Gap_Score.xlsx`). Feature thứ 1 ($\Delta$) đã sẵn sàng.

---

## 🔵 LUỒNG 2 (THREAD 2): ĐÁNH GIÁ ĐỘ TẬP TRUNG ESG BẰNG TF-IDF

**Vị trí file:** `d:\NCKH\Thread_2\GSI_Calculation.ipynb`

### 1. Ý nghĩa của luồng này
Luồng 2 chỉ phân tích văn bản nội bộ (Report). Mục tiêu là đo lường mức độ "đậm đặc" các nỗ lực Môi trường (E), Xã hội (S), và Quản trị (G) mà ngân hàng tự tuyên bố. 

- Thuật toán đọc bộ Từ điển ESG (từ 3 file Excel `E.xlsx, S.xlsx, G.xlsx`).
- Đối chiếu vào file văn bản thô (text) của Báo cáo.
- Tính ra điểm **TF-IDF Raw (Điểm thô)** cho từng khía cạnh $E$, $S$, $G$. **Lưu ý:** Chúng ta lấy điểm thô thay vì chuẩn hóa về `[0, 1]` nhằm bảo toàn độ lớn/nhỏ thực tế giữa các báo cáo, đảm bảo sự công bằng khi đưa vào mô hình Clustering chéo giữa nhiều ngân hàng.

### 2. Cách chạy Code
1. Mở file `GSI_Calculation.ipynb`.
2. Mở `Cell 4` (Cấu hình) và đổi đường dẫn `REPORT_TEXT_FILE` trỏ tới file văn bản thô của Báo cáo bạn cần đo.
   - Ví dụ: `REPORT_TEXT_FILE = r"D:\NCKH\ESG_reporting\extracted_texts\BIDV_2023_ESG_raw.txt"`
   *(Thuật toán được thiết kế thông minh để tự động nhận dạng Bank Name và Năm từ tên file nếu file được đặt tên dạng `TênBank_Năm_ESG...`)* 
3. Chạy toàn bộ Notebook (**Run All**).
4. **Kết quả (Output):** Tự động sinh ra cấu trúc thư mục dạng `Thread_2/outputs/{Năm}/{Bank}/`. Bên trong gồm:
   - File JSON/CSV chứa kết quả 3 Feature tiếp theo: $E\_Score$, $S\_Score$, $G\_Score$.
   - Một biểu đồ cột Bar Chart trực quan ($GSI\_Report.png$).

---

## ⏭️ BƯỚC CUỐI (TƯƠNG LAI): GOM DỮ LIỆU & PHÂN CỤM (CLUSTERING)

Sau khi bạn đã thực hiện [BƯỚC 1] và [BƯỚC 2] lặp lại cho toàn bộ X ngân hàng trong tập dữ liệu của bạn, chúng ta sẽ bắt đầu khởi tạo Luồng 3.

**Quy trình dự kiến:**
1. Thuật toán tự động đọc tất cả file từ Output của Luồng 1 ($\Delta$) và Luồng 2 ($E, S, G$).
2. Trải phẳng dữ liệu vào 1 bảng (Master DataFrame) duy nhất gồm 5 cột: 
   `['Bank_Name', 'Delta_Gap', 'E_score', 'S_score', 'G_score']`
3. Gọi hàm `StandardScaler()` để chuẩn hóa đồng nhất 4 feature (Vì đơn vị của Delta và TF-IDF khác nhau hoàn toàn).
4. Đẩy bảng đã chuẩn hóa vào mô hình **K-Means Clustering** (hoặc Hierarchical Clustering). 
5. Phân nhóm ngân hàng thành 3 nhãn: 
   - **High Greenwashing Risk** (Rủi ro cao)
   - **Medium Greenwashing Risk** (Rủi ro trung bình)
   - **Low Greenwashing Risk / Credible** (Đáng tin cậy)