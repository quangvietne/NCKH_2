import pandas as pd
import numpy as np

def clean_data(input_file, output_file):
    # 1. Đọc dữ liệu từ file Excel
    print(f"Đang đọc dữ liệu từ: {input_file}")
    df = pd.read_excel(input_file)
    print(f"Số lượng ngân hàng ban đầu: {len(df)}")

    # 2. Xử lý giá trị trống (NaN) thành 0 để đồng bộ
    df['Report_Score_X'] = df['Report_Score_X'].fillna(0)
    df['News_Score_Y_mean'] = df['News_Score_Y_mean'].fillna(0)

    # 3. Lọc dữ liệu: 
    # Giữ lại những hàng mà cả Report_Score_X VÀ News_Score_Y_mean ĐỀU PHẢI KHÁC 0
    # Nghĩa là nếu 1 trong 2 cột bằng 0 (hoặc bị trống), hàng đó sẽ bị xóa.
    condition = (df['Report_Score_X'] != 0) & (df['News_Score_Y_mean'] != 0)
    df_cleaned = df[condition].copy()

    # Nếu bạn chỉ muốn xóa khi CẢ 2 đều bằng 0, hãy đổi thành:
    # condition = ~((df['Report_Score_X'] == 0) & (df['News_Score_Y_mean'] == 0))

    giam_su_luong = len(df) - len(df_cleaned)
    print(f"Đã xóa {giam_su_luong} hàng có giá trị Report_Score_X hoặc News_Score_Y_mean bằng 0/trống.")
    print(f"Số lượng ngân hàng còn lại để phân cụm: {len(df_cleaned)}")

    # 4. Lưu ra file mới
    df_cleaned.to_excel(output_file, index=False)
    print(f"Đã lưu dữ liệu sạch vào: {output_file}")

import os

if __name__ == "__main__":
    # Tự động lấy thư mục Thread_3 chứa file code này
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    INPUT_PATH = os.path.join(BASE_DIR, 'Combined_Features.xlsx')
    OUTPUT_PATH = os.path.join(BASE_DIR, 'Combined_Features_Cleaned.xlsx')
    
    clean_data(INPUT_PATH, OUTPUT_PATH)
