# BÁO CÁO PHƯƠNG PHÁP LUẬN: MÔ HÌNH HỌC MÁY PHÁP HIỆN RỦI RO TẨY XANH (GREENWASHING)

*(Định dạng văn phong học thuật chuẩn Tạp chí Q1 - ISI/Scopus)*

## 1. Cơ sở lý thuyết của Lựa chọn Đặc trưng (Feature Selection)

Trong các nghiên cứu trước đây, việc đo lường Tẩy xanh thường chỉ dừng lại ở phân tích một chiều (đơn biến) bằng cách đo lường khoảng cách giữa tính minh bạch và thực tế. Tuy nhiên, để cấu trúc hóa toàn diện "hành vi pháp lý" của một tổ chức tín dụng, nghiên cứu này đề xuất một không gian vectơ 7 chiều (7-dimensional Feature Space) nhằm đạt được sự "tam giác đạc" (Triangulation) thông tin:

* **Report_Score_X & News_Score_Y_mean:** Đại diện cho hai lăng kính đối lập - Nỗ lực phô trương chủ quan (Báo cáo) và Sự giám sát khách quan từ công chúng (Báo chí).
* **Delta_Gap ($X - Y$):** Hệ số cốt lõi định lượng quy mô của hành vi "Tẩy xanh". Giá trị dương càng lớn, mức độ phóng đại thành tích càng nghiêm trọng.
* **E_tfidf, S_tfidf, G_tfidf:** Bộ trọng số phân bổ sự tập trung (Thematic Focus). Nghiên cứu cho rằng hành vi Tẩy xanh không phân bổ đều. Việc đưa 3 biến này vào giúp mô hình thấu hiểu "chiến lược" của ngân hàng (Ví dụ: Ngân hàng có xu hướng tẩy xanh chỉ nhắm vào nhóm "Môi trường" để dễ lấy danh tiếng, trong khi ngó lơ "Quản trị").
* **GSI_Raw:** Đại diện cho năng lực Bền vững Tổng thể. Biến này phân định rõ sự khác biệt giữa một ngân hàng "Yếu kém nhưng trung trực" và một ngân hàng "Khá tốt nhưng vẫn phóng đại".

## 2. Ý nghĩa của Tiền xử lý Phân tích Khám phá (EDA - Exploratory Data Analysis)

Trước khi đưa vào mô hình Học máy, Thống kê Khám phá (EDA) phân phối được tiến hành để xác thực các giả định ban đầu:

* **Ma trận tương quan (Pearson Correlation Matrix):** Kiểm định hiện tượng đa cộng tuyến (Multicollinearity). Nếu `Delta_Gap` biến thiên tương đương 1.0 với `Report_Score_X`, thuộc tính sẽ bị loại bỏ. Tuy nhiên, EDA chứng minh sự độc lập tương đối giữa cấu trúc cấu thành (TF-IDF) và khoảng cách hành vi (Delta_Gap).
* **Mật độ phân phối (KDE - Kernel Density Estimation) & Boxplot:** Kết quả EDA phơi bày sự bất bình đẳng khổng lồ về phương sai (Variance) giữa các biến số. Trong khi `GSI` hoặc `Delta_Gap` có độ dao động rất lớn, các chỉ số cắt lớp văn bản `TF-IDF` lại dao động với biên độ siêu vi mô ($10^{-3}$). Điểm này đặt ra yêu cầu tiên quyết về phép chuyển đổi tỷ lệ chiều không gian (Dimensional Scaling).

## 3. Lựa chọn Chuẩn hóa Z-Score (Standardization thay vì Min-Max Scaler)

Trong nghiên cứu Dữ liệu Khoa học Môi trường, thuật toán phân cụm dựa trên đo lường Khoảng cách (Euclidean Distance). Việc tồn tại lệch chuẩn phương sai (Variance Bias) sẽ khiến mô hình bị thao túng bởi các biến có Scale lớn (Delta_Gap) và triệt tiêu tính chất rành mạch của các biến cấu trúc (TF-IDF).

* **Tại sao không dùng Min-Max Scaler ($[0,1]$)?** Việc ép dữ liệu vào khoảng $[0,1]$ triệt tiêu độ giãn của các giá trị ngoại lệ (Outliers). Trong khi đó, bản chất cốt lõi của việc đi tìm "Tẩy xanh" chính là đi tìm các **Giá trị ngoại lệ cực đoan (Anomalies)**.
* **Giải pháp Z-Score (StandardScaler):** Phép biến đổi $z = (x - \mu) / \sigma$ kéo trung bình phân phối tổng thể về $0$ và độ lệch chuẩn bằng $1$. Phép toán này cung cấp một thước đo trung lập: "Một ngân hàng mang hành vi chệch hướng bao nhiêu đơn vị so với chuẩn mực chung của toàn ngành kinh tế?". Điều này bảo toàn hoàn hảo các giá trị ngoại lệ, giúp thuật toán phân tách khoảng cách bạo chi (Tẩy xanh) nhạy bén hơn.

## 4. Lựa chọn Thuật toán Hierarchical Agglomerative Clustering (HAC)

Nghiên cứu từ chối sử dụng thuật toán phổ biến K-Means do giới hạn về tính tiền giả định (áp đặt số lượng K cụm từ đầu) và nhạy cảm với khởi tạo tâm cụm cục bộ (Local Minima). Thay vào đó, **Phân cụm Không gian Phân cấp (Hierarchical Clustering)** kết hợp phương pháp **Ward's Minimum Variance** được ưu tiên triển khai vì các cơ sở khoa học sau:

* **Tính khách quan của cấu trúc (Topology):** Thuật toán sử dụng hướng tiếp cận Từ dưới lên (Bottom-up). Khởi đi từ việc coi N=26 ngân hàng là 26 thực thể độc lập, mô hình tính toán Ma trận khoảng cách để liên tục hợp nhất nhóm sao cho **Tổng bình phương sai số nội cụm (Within-Cluster Sum of Squares - WSS)** tăng lên ít nhất ở mỗi bước.
* **Quyết định số cụm (K) bằng Dendrogram Heuristic:** Biểu đồ cây phả hệ (Dendrogram) mang lại bằng chứng toán học trực quan về cấu trúc liên kết vi mô của ngành ngân hàng. Việc đặt nhát cắt (Horizontal Cut) sinh ra $K=3$ cụm được chứng minh dựa trên điểm ngắt đoạn (longest vertical distance) tự nhiên nhất, triệt tiêu hoàn toàn sự can thiệp chủ quan của nhà nghiên cứu.

## 5. Giải nghĩa Kết quả Cụm (Cluster Interpretation & Validation)

Sau khi hợp nhất các tập dữ liệu, kỹ thuật Auto-Profiling phân tích các Tâm cụm (Centroids) và quy hoạch Ngành Ngân hàng thành 3 Typology (Kiểu hình) chính:

1. **🔴 Nhóm Rủi ro Tẩy xanh Tương đối Cao (Severe Greenwashing Risk):** Đặc trưng bởi chỉ số `Delta_Gap` cao vượt ngưỡng dương. Đây là hạt nhân của hành vi thổi phồng công trạng trên Báo cáo Phát triển Bền vững, đối nghịch hoàn toàn với sự xác thực từ lăng kính Truyền thông Đại chúng.
2. **🟡 Nhóm Rủi ro Tiềm ẩn (Latent Risk):** Đại diện cho khối giao thoa, sự chênh lệch `Delta_Gap` biểu hiện nhưng chưa đạt mức độ phi chuẩn (Anomaly). Phản ánh thực trạng báo cáo còn mù mờ, thiếu khung đánh giá nhất quán.
3. **🟢 Nhóm Chân thực/Ít Rủi ro (Authentic Sustainability):** Tâm cụm có `Delta_Gap` hội tụ về $0$ hoặc âm. Điều này củng cố năng lực Bền vững thực chất khi mức độ tuyên bố nội bộ đồng biên độ với ghi nhận từ dư luận.

**Kiểm định thị giác (Dimensionality Reduction & Validation):**
Do dữ liệu gốc nằm ở cấu trúc $R^7$ không thể quan sát, nghiên cứu ứng dụng phép Thu gọn chiều PCA (Principal Component Analysis) và Đồ thị không gian Thực tế vs Hành vi (`GSI_Raw` ngang giá với `Delta_Gap`). Hai hệ trục này chứng minh ranh giới của 3 cụm phân hóa rạch ròi, độc lập, không chồng lấp. Khẳng định hiệu suất và độ tin cậy thống kê (Robustness) của mô hình HAC trong việc trích xuất và đo lường hành vi "Tẩy xanh" trong báo cáo kinh tế.
