# Báo Cáo Giải Quyết Tình Huống Airbnb: Trả Lời Chuyên Sâu Các Câu Hỏi Phân Tích

Dưới đây là phần trình bày chi tiết và trực tiếp cho 6 câu hỏi yêu cầu trong bài tập tình huống phân tích giá thuê nhà Airbnb tại Bondi Beach, bao gồm các hình ảnh minh họa về dữ liệu thực tế.

---

## 1. Describe the dataset and the problem statement, what is the nature of this case?
**(Mô tả bộ dữ liệu, phát biểu bài toán và chỉ ra bản chất của case này)**

* **Bộ Dữ Liệu (The Dataset)**: Tập dữ liệu `airbnb.csv` bao gồm thông tin của hàng chục nghìn căn hộ Airbnb tại khu vực Sydney. Hệ thống ban đầu ghi nhận 85 cột hỗn hợp (văn bản mô tả `description`, đường link `listing_url`, tọa độ địa lý `latitude/longitude`, đánh giá `review_scores`, giá thuê `price`, phí dọn dẹp `cleaning_fee`,...). Phần lớn các căn hộ phục vụ phân khúc bình dân, tuy nhiên phân phối giá có độ tản mác rất cao với các "siêu biệt thự" đẩy đuôi giá thị trường lên dài.
* **Phát biểu bài toán (Problem Statement)**: Khách hàng sở hữu một căn siêu biệt thự (sức chứa 10 người, 5 phòng ngủ, 3 phòng tắm, tiền cọc lên tới $1500) nằm tại khu vực biển Bondi Beach sầm uất. Hiện tại họ đang thắt chặt giá thuê ở mức **$500/đêm**. Yêu cầu cốt lõi là làm sao để sử dụng dữ liệu thị trường làm thước đo, xây dựng mô hình "Định giá chuẩn (Fair Value dự kiến)" cho căn hộ này. Từ đó xác định xem mức $500 là đắt hay rẻ so với thị hiếu, và tư vấn một chiến lược giá tối đa hóa doanh thu.
* **Bản chất của tình huống (Nature of this case)**: Đây là một bài toán tiêu biểu của **Khai phá dữ liệu (Data Mining)**, đi kèm với **Phân tích dự báo (Predictive Analytics)** trên Dữ liệu Bất động sản (Real Estate). Cụ thể, yêu cầu quy trình: 
  * Xử lý Tiền xử lý dữ liệu phức tạp (Data Preprocessing & Cleaning).
  * Mô hình hóa **Hồi quy (Regression Modeling)** để dự đoán một biến liên tục (Giá tiền - Price).
  * Tinh chỉnh thuật toán (Tuning) để đối phó với dữ liệu dị biệt (Outliers).

---

## 2. Does data have any defects or issues? State the solution if any!
**(Dữ liệu có khiếm khuyết hay vấn đề gì không? Hãy nêu giải pháp nếu có!)**

Hệ thống ghi nhận 3 "vết rách" dữ liệu (Data defects) vô cùng nghiêm trọng. Dưới đây là bảng minh họa lỗi và giải pháp tương ứng:

### A. Lỗi hỏng cấu trúc phân tách (CSV Corruption) 
* *Vấn đề*: Trong các cột văn bản dài như `description` hay `reviews`, tác giả có sử dụng Enter "xuống dòng" (`\n`) hoặc có dấu phẩy `,` nhưng thư viện mặc định không bọc (escape) đoạn văn này bằng dấu Quote `""` đúng chuẩn. Hậu quả là: 1 đoạn văn chứa dấu phẩy bị cắt làm 2 cột riêng biệt, "đẩy" các số liệu phía sau lệch vị trí hoàn toàn.
* **Minh họa sự xô lệch (Dữ liệu Thô):**
  | id | listing_url | name | description | ... | price |
  |---|---|---|---|---|---|
  | 11156 | https://.../11156 | An Oasis in the City | "This is a great place, very near to the beach, \n I loved it here..." | ... | *(Bị đẩy sang cột khác, mất dữ liệu)* |
* *Giải pháp*: Xây dựng thuật toán Python thuần (Custom Parser bằng Regex và `csv.reader`) rà soát từng dòng text lỗi, khôi phục vỏ Quote `""` để nhốt các dấu phẩy bên trong, sau đó loại bỏ sạch 100% cột chứa chữ. **Lấy lại được ma trận số nguyên vẹn 22,992 dòng:**
  | room_id | latitude | longitude | accommodates | bathrooms | bedrooms | price ($) | security_deposit |
  |---|---|---|---|---|---|---|---|
  | 11156 | -33.8693 | 151.2268 | 1 | 1.0 | 1.0 | **65.0** | 150.0 |
  | 14250 | -33.8009 | 151.1766 | 6 | 3.0 | 3.0 | **469.0** | 900.0 |

### B. Dữ liệu định dạng sai thể loại (Data Type Error)
* *Vấn đề*: Tiền tệ bị dính kí tự string (ví dụ `$1,500.00`). URL (chuỗi ký tự) không thể cho vào mô hình tính toán. Biến True/False bị ghi bằng mã ký tự `t`/`f`.
* *Giải pháp*: Regex cắt mã số phòng từ `listing_url` thành biến định danh `room_id`. Xóa kí tự `$`, `,` và ép kiểu về Float64. Áp dụng hàm Mapping chuyển đổi các biến `host_is_superhost` từ `t/f` thành binary `1/0`.

### C. Nhiễu giá trên trời, Phân phối Lệch Phải (Right-Skewed Outliers)
* *Vấn đề*: Vì có quá nhiều siêu biệt thự ($5000 - $10,000/đêm), đường cong giá bị kéo dãn tạo hình cái đuôi dài thòng, vi phạm giả định phân phối chuẩn của các mô hình Hồi quy.
* *Giải pháp*: Loại bỏ Top 1% ngoại lai cực đại (Outliers). Bắt buộc áp dụng Thuật toán chuẩn hóa chịu lực **RobustScaler** (Chống nhiễu tốt hơn StandardScaler) và hàm **Log-Transform `y = log(1 + price)`** lên cột giá tiền để ép đường cong về hình chuông.

---

## 3. What kind of model could be used in this case? Explain!
**(Loại mô hình nào có thể được sử dụng trong trường hợp này? Giải thích!)**

Karena mục tiêu là ước lượng/dự đoán để sinh ra một con số cụ thể mang tính định giá (Price), kỹ thuật xương sống bắt buộc phải dùng là nhóm **Thuật toán Hồi quy (Regression Models)**. Nếu muốn trả lời câu hỏi "Đắt hay Rẻ", ta có thể chuyển thể nó thành bài toán Phân loại nhãn (Classification) với ngưỡng là Giá trị Trung vị (Median).

**Các mô hình phù hợp và nhận định của Analyst:**
1. **Mô hình tuyến tính cơ sở (Linear Regression, Ridge, Lasso)**:
   * Có thể làm Baseline. **Tuy nhiên**, Linear Regression sẽ thất bại thê thảm nếu áp dụng thực tế trên bộ Dữ liệu này. Giả định của Linear là các đường thẳng dốc. Khi gặp cấu hình nhà khủng của khách hàng ở Bondi (10 chỗ, 5 phòng), đường dốc sẽ phóng hệ số (slope) đi thẳng lên trời, báo kết quả dự báo siêu thực tế lên tới hàng triệu đô!
2. **Hồi quy Đa thức (Polynomial Regression)**:
   * Giúp xem xét tương tác đa chiều. Nhưng nếu dùng trên quá bậc 3 (Deg > 3), dữ liệu sinh ra **Bùng nổ chiều kích (Curse of Dimensionality)**, nội suy ra phương trình âm $\$-1.
3. **Mô hình Rừng ngẫu nhiên (Random Forest Regressor)**:
   * **ĐÂY TẤT YẾU LÀ MÔ HÌNH NHÀ VUA TRONG NGÀNH BẤT ĐỘNG SẢN.** 
   * *Giải thích*: Giá nhà chưa bao giờ mang tính chất tăng theo đường thẳng (Non-linear). Tiền dọn phòng của 5 phòng không có nghĩa là gấp 5 lần tiền dọn của 1 phòng. Random Forest tạo ra hàng vạn Cây Quyết Định (Decision Trees), phân rẽ dữ liệu qua các ngưỡng điều kiện `if/else`, đóng khung và khoanh lô vùng giá. Do đó, thuật toán này tuyệt đối KHÔNG phóng đại đường cong ra vô cực như Linear, mà đưa ra một giới hạn khống chế hoàn toàn ổn định.

---

## 4. Perform data exploratory analysis (you could use descriptive analysis or charts)!
**(Tiến hành phân tích khám phá dữ liệu trực quan bằng biểu đồ)**

Quá trình EDA đã trả về các đặc tính trực quan giải thích được bộ khung thị trường Airbnb của Sydney:

1. **Phân phối giá phòng (Price Distribution):** Phần lớn căn hộ Airbnb thuộc phân khúc giá dưới $200. Việc xuất hiện các ngoại lai làm đồ thị dãn mạnh sang tay phải (Right-Skewed).
![Price Distribution](./price_distribution.png)

2. **Ma trận tương quan (Correlation Matrix):** Phân tích sự đồng biến cho thấy biến mục tiêu `price` (dòng/cột cuối) đỏ sậm khi chiếu với `accommodates` (sức chứa), `bedrooms` (số phòng ngủ) và `cleaning_fee` (phí dọn phòng). Đây là 3 trụ cột thiết lập giá.
![Correlation Matrix](./correlation_matrix.png)

3. **Luật bậc thang (Price vs Accommodates):** Biểu đồ Boxes minh chứng chân lý hiển nhiên trong ngành lưu trú: Căn hộ cho phép chứa càng nhiều khách thì giá trung vị Median (đường ngạch ngang trong hộp) lại càng tăng tiến liên tục, mở rộng biên độ phương sai.
![Price vs Accommodates](./price_vs_accommodates.png)

4. **Bản đồ Nhiệt Giá (Price Map):** Chấm dải vị trí địa lý theo tọa độ Latitude / Longitude. Những cụm màu sáng nhất / cam rực rỡ nhất (giá đắt nhất) bám dính dày đặc vào trung tâm kinh tế Sydney (CBD) và Vùng biển lướt sóng Bondi Beach. Càng ra vùng rìa, màu xanh biển (giá rẻ) càng áp đảo.
![Price Map](./price_map.png)

---

## 5. Is there any special point or potential issue that the analyst must pay attention to?
**(Có điểm đặc biệt hay vấn đề tiềm ẩn nào mà Analyst cần chú ý không?)**

Đây là một bài phân tích mà chỉ cần Data Analyst lơ là, mọi kết quả mô hình sẽ là rác. Có **5 Cạm Bẫy Trí mạng (Special Points)** Analyst bắt buộc phải thuộc lòng:

1. **Sát thủ Ngoại suy (Extrapolation Hazard)**: 
   Căn hộ mục tiêu ở Bondi là dạng siêu biệt thự quá hiếm hoi (10 người ở, cọc $1500, diện tích khủng). Nó bứt lìa khỏi phần đông Dữ liệu Training. Mô hình tuyến tính khi bị ép phải đoán "ngoài vùng phủ sóng", nó sẽ vẽ đường thẳng kéo dãn sai số ra vô cực (đoán ra mức $5280/đêm — gấp 10 lần giá trị thực!). 
   *(Minh họa: Điểm đỏ của Bondi chót vót nằm ngoài vùng xanh của Market Data)*
   ![Extrapolation Risk](./q5_extrapolation_risk.png)

2. **Lời nguyền hỏng Metric RMSE vì biến Tần số lệch (Right-Skewed Target)**: 
   Đồ thị Histogram giá gốc bị lệch. Metric RMSE phạt rất nặng những "sai số lớn" bằng sức mạnh "bình phương" sai số. Hệ thống sẽ bị 1 căn siêu xe $10,000 kéo toàn bộ RMSE trung bình của hệ thống lên mức vô lý (kém tin cậy).
   **Giải pháp cứu mạng**: Sử dụng **Log-Transform**. Hệ thống sẽ đổi `y = log(1 + price)`. Như hình đồ thị dưới, dữ liệu Logarit đã được nén về lại cấu trúc Phân phối chuẩn Hình Chuông (Bell Curve) hoàn mỹ! 
   ![Price Skewness](./q5_price_skewness.png)

3. **Vỡ trận nếu tin tưởng mù quáng vào Pandas `on_bad_lines="skip"`**: 
   Nếu gặp dữ liệu lỗi CSV, lệnh Skip sẽ làm bay mất toàn bộ những review dài. Hoặc nếu bạn gượng ép điền khuyết `fillna()` với giá trị rẻ rúng mà không Parser Text, bạn đang tự bẻ cong hệ số. Bắt buộc viết script Parser.

4. **Bi kịch Overfitting của mô hình Đa thức (Polynomial Curse of Dimensionality)**: 
   Khi tăng Đa thức lên bậc 6-10 trên 3 biến, phép tính kết tụ cấp số nhân liên tục tạo ra các trọng số rác (Weight Explosion). Model dự báo bằng toán học ra giá trị **âm** đối với giá nhà trên tập Test. 

5. **Giải bài phán xét của Hệ thống Mô Hình hóa**: 
   Qua hình vẽ dưới đây (Biểu đồ log-scale Mức giá dự đoán căn Bondi), rõ ràng chỉ có mô hình Rừng Cây (Tree-based Random Forest) là đứng vững, kìm hãm thành công đà tăng xằng bậy của Linear, trong khi Polynomial đã nổ tung (giá âm) và Linear Regression phóng đại lên hàng triệu đô la.
   ![Model Predictions](./q5_model_predictions.png)

---

## 6. Bonus: Perform the model to solve the problem, discuss the result, make conclusions or recommendations
**(Thực hiện bằng Code để giải quyết, Bàn luận kết quả, Phân tích Kết luận & Lời khuyên cuối cùng)**

### A. Thực Thi Code Mô Hình (Log-Transform & RobustScaler)
Dưới sự trợ lực từ thư viện `sklearn`, dữ liệu được xử lý qua 2 bước tối thượng: `RobustScaler()` (Chế ngự nhiễu ngoại suy) và Log-Target. Kết quả trích xuất các thông số thuật toán cho căn biệt thự mục tiêu tại Bondi như sau:

| Thuật Toán Mô hình (Model) | Độ lệch chuẩn tối thiểu (RMSE) | R² Score | Mức giá dự đoán cho căn hộ Bondi |
|---|---|---|---|
| **Random Forest Regressor** | **103.09** (Tốt nhất) | **0.65** | **$615.36 / đêm** |
| Lasso Regression (Phạt L1) | 126.88 | 0.47 | $918.50 / đêm |
| Ridge Regression (Phạt L2) | 130.99 | 0.43 | ~$8 Triệu $ (Hỏng) |
| Linear Regression Core | 130.99 | 0.43 | ~$8 Triệu $ (Hỏng) |
| Polynomial Reg (Bậc 6) | 121.91 (Trên Test) | N/A | Bị âm giá / Lỗi số học |

### B. Bàn Luận (Discussion) & Đưa Ra Kết Luận (Conclusion)
* **Trực quan hiệu suất kỹ thuật (Performance Breakdown):** Việc dũng cảm thay đổi cơ chế Scaling và ép hệ phương trình Logarit đã **giảm RMSE của Random Forest từ một mốc tồi tệ (266) chìm thẳng xuống còn 103** (Cải thiện độ chính xác ròng rã hơn 60%). Chỉ số R² thể hiện độ chặt của mô hình nhân đôi lên **0.65**. Random Forest, như đã khẳng định ở Câu 3 và Câu 5, là ông vua tuyệt đối cho Data Bất động sản này.
* **Định mức chuẩn hệ thống:** Với ma trận tính toán độ nặng của (10 sức chứa + 5 phòng ngủ + Biển Bondi + Siêu cọc $1500), thuật toán máy học RF tốt nhất đã chốt định giá "Công bằng - Fair Value" cho căn hộ này tại thị trường địa phương là **$\sim\$615.36** /đêm.

### C. Khuyến Nghị Hành Động (Actionable Recommendations)
* **Phán xét đối với mức giá Chủ Nhà đang đặt:** Hiện tại, giá khách cấu hình $500/đêm là một sự **THẤT THU (Undervaluation)**. Hệ thống mô hình đã dọn sạch các căn ảo báo hiệu giá trị lô đất và số lượng sức chứa khổng lồ này có thể gánh vác mức giá cao hơn rất nhiều.
* **Tư vấn Lộ trình Tăng trưởng (Revenue Strategy):** Tạm coi $500 là chiêu bài Marketing hạ giá ban đầu nhử khách (Host đã rất thành công nhận Rating 95.0 với 53 lượt đánh giá và lên Superhost). Đã đến lúc gặt hái thành quả! Chuyên viên Phân tích Dữ liệu khuyến nghị Host nên **KÍCH HOẠT TĂNG GIÁ** tịnh tiến dần từ **$600 đến $650 /đêm**. 
* Lộ trình này sẽ mang lại cho chủ nhà biên thu nhập tăng ròng khoảng `+$100` đến `+$150` mỗi ngày mà vẫn vô cùng vững chãi bám sát biểu đồ cạnh tranh khu vực của Airbnb!
