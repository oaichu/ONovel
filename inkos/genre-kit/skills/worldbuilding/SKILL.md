---
name: worldbuilding
description: Dùng khi cần xây dựng hoặc kiểm tra tính nhất quán của thế giới huyền huyễn, tiên hiệp, cổ đại, hiện đại; thiết lập cảnh giới, tông môn, kinh tế-chính-trị, quy tắc, story bible; hoặc khi sợ "lật kèothiết lập", thế giới chết cứng, nhân vật bay nhảyphớt lờ quy tắc.
---

# Xây dựng thế giới (Worldbuilding)

## Mục đích

Biến ý tưởng thành một **bộ hồ sơ thế giới có thể tra cứu, có thể cập nhật, có thể ràng buộc nhân vật**, thay vì mớ bối cảnh nhớ trong đầu rồi quên. Thế giới tốt là nền tảng cho sảng điểm và phục bút, không phải bảo tàng trưng bàythiết lập.

Nguyên tắc cốt lõi:
- **Hồ sơ là nguồn sự thật duy nhất**: định rồi thì đối chiếu khi viết; muốn sửa phải sửa hồ sơ trước rồi mới sửa bản thảo.
- **Đặt luật trước, giữ luật sau**: ví dụ đã quy "hỏa hệ dưới mưa giảm thương", cả sách phải chấp nhận.
- **Thế giới phải sống**: cập nhật trạng thái theo chương, không để bối cảnh hóa đá.
- **Vừa đủ thôi**: thiết lập mạnh vẫn phải phục vụđọc theo dõi, thế giới là móng nhà không phải triển lãm.

## Khi nào dùng

- Mở truyện thuộc tuyến **thế giớitiên phong**: huyền huyễn, tiên hiệp, tiên hiệp cổ đại, chiến tranh,cuối thế, lịch sử, esports; tức là quy tắc thế giớibản thân đã là điểm bán.
- Sợ ba triệu chứng kinh điển: viết tới đoạn thế giớitrước sau không nhất quán; nhân vật bay nhảy vô địch bỏ qua luật mình đặt; đi tới nơi mà chương trước đã miêu tả nơi đó bị phá hủy hoặc chưa từng xuất hiện.
- Cần để thế giới **đổi trạng thái theo cốt truyện**: chiến tranh bùng nổ, thành thị hư hại, tông môn suy vong, triều đình thay chủ.
- Cần dựng **story bible** (cẩm nang truyện) làm tài liệu nền cho nhiều chương/tập.
- Phân công với kỹ năng liên quan: `worldbuilding` dựng quy tắc thế giới; kim thủ chỉ (kim chỉ) lo ngoạichết của nhân vật; đại cương lo mạch truyện; ghi nhớ lo lưu trữ; kiểm tra liên tục lo soát lỗi.

Nếu truyện là **nhân vậttiên phong** (ngôn tình, đô thị cảm tình, truyện ngắn), thế giới chỉ cần mức nhất quán tối thiểu: địa lý, thời gian, quy tắc đừng xuyên tạc là đủ, một câu thiết lập là xong.

## Quy trình

### Bước 1: Chọn mô-đun thế giới cần dựng

Tùy thể loại, phủ các khối sau. Mỗi mục cấp **một nhãn duy nhất** dạng `#luc-luc-ky` hay `#the-luc-mon-phai` để tra cứu chéo khi viết:

| Mô-đun |điểm mấu chốt | Ví dụ nhãn |
|---|---|---|
| Lực lượng / võ học / ma pháp | thang cảnh giới (cảnh giới), quy tắc thi triển, giới hạn trên, cái giá phải trả | `#luc-luc-ky` |
| Chủng tộc / thế lực | lập trườngcác bên, mạnh yếu, quan hệ với nhân vật chính | `#the-luc-mon-phai` |
| Thể chế chính trị | ai nắm quyền, luật lệ, điều cấm kỵ | `#chinh-tri-hoang-quyen` |
| Thể chế kinh tế | tiền tệ, tài nguyên, vật phẩm khan hiếm (linh thạch, lương thảo, chip...) | `#kinh-te-linh-thach` |
| Địa lý bản đồ | địa điểm trọng yếu, khoảng cách, phạm vi thế lực | `#dia-ly-bac-thanh` |
| Đại sự ký lịch sử | chuyện gì xảy ra trước khi mở truyện, phục bút để lại | `#su-mon-phai` |

Mỗi mục ghi đủ bốn phần: **nhãn + mô tả + quy tắc (có thể kích hoạt/trích dẫn) + dòng thời gian liên quan**.

### Bước 2: Dựng trạng thái thế giới sống (World State)

Ghi trạng thái trọng yếu theo chương, treo lên dòng thời gian:

```
# Trạng thái thế giới (cập nhật theo chương)
Chương 1: chiến tranh=bùng nổ; thành Bắc hư hại=20%; nhân vật chính=đã vào thành Bắc
Chương 8: thành Bắc hư hại=60%; đường lương=đứt; tông môn Thiên Kiếm=đóng sơn môn
Chương 12: thành Bắc thất thủ; dân thường di cư về nam
```

Lợi ích: hành vi nhân vật **phụ thuộc trạng thái thế giới**, chặn lỗi "đi mua trang bị ở thành Bắc nhưng thành Bắc chương trước đã bị phá".

### Bước 3: Gắn nhân vật vào quy tắc thế giới

- **Năng lực phải nằm trong hệ thống**: thương của một chiêu hỏa kiếm phải có biên độ, dưới mưa hoặc địa hình thủy thuộc phải giảm; đừng vô hiệu hóa luật mình đặt.
- **Hành động bị địa lý-chính trị trói**: đi tới nơi phải có lộ trình, phải xin thông quan, phải tránh thế lực nào đó, không được dịch chuyển coi như không có gì.
- **Sự kiện có thể kích hoạt phụ thuộc trạng thái**: thành Bắc thất thủ thì tuyến "mua trang bị ở thành Bắc" tự hủy.

### Bước 4: Bốn câu hỏi thế giới trước khi viết chương

Trước mỗi chương N, trả lời rồi mới nhét vào prompt viết:

1. Trạng thái thế giới hiện tại là gì? (dòng mới nhất trong dòng thời gian)
2. Nhân vật chínhlúc này làm được gì, không làm được gì? (bị hệ thống, địa lý, chính trị, tài nguyên hạn chế)
3. Xung đột của chương có mọc ra từ quy tắc thế giới không? (không phải chèn từ trên trời)
4. Môi trường, thời tiết, địa hình ảnh hưởng thế nào tới cảm xúc hoặc chiến đấu của chương? (để môi trường đẩy cốt truyện, đừng chỉ tả cảnh)

### Bước 5: Dựng story bible (cẩm nang truyện)

Tập hợp thành một tài liệu tra cứu, gồm các khối:

- **Thông tin cơ bản**: tên tạm, thể loại, thể loại con, đối tượng độc giả, mục tiêu chữ, số chương dự kiến.
- **Premise**: logline một câu, pitch 2-3 đoạn, câu hỏi trung tâm truyện trả lời.
- **Chủ đề**: chủ đề chính, chủ đề phụ, cung phát triển chủ đề.
- **Bối cảnh**: thời kỳ, địa điểm trọng yếu (mô tả, không khí, vai trò), quy tắc thế giới (cơ chế, giới hạn, cái giá, luật thành văn), cấu trúc xã hội-chính trị (ai nắm quyền, chuẩn mực, nguồn xung đột).
- **Dàn nhân vật**: nhân vật chính, phản diện, tuyến phụ quan trọng, gắn với hồ sơ chi tiết.
- **Cấu trúc**: chia hồi, danh sách chương.
- **Tuyến cốt truyện**: chính tuyến và các phụ tuyến, mô tả và kết cục từng tuyến.
- **Giọng văn**: tông truyện, ngôi kể, thì, phong cách văn tự, tác phẩm tương đồng để tham chiếu.
- **Ghi chú nghiên cứu** và **xem xét tương lai** (tiềm năng phần tiếp, spin-off).

### Bước 6: Chọn thứ tự thế giớitiên phong hay nhân vậttiên phong

- **Thế giớitiên phong**: huyền huyễn, tiên hiệp, lịch sử, chiến tranh,cuối thế, esports. Quy tắc làđiểm bán, dựng thế giới trước.
- **Nhân vậttiên phong**: ngôn tình, đô thị cảm tình, truyện ngắn. Cảm xúc làđiểm bán, dựng nhân vật trước, thế giới vừa đủ.
- Dù nhân vậttiên phong, truyện dài vẫn cần **tính nhất quán thế giới tối thiểu**.

### Bước 7: Cách lồng thiết lập vào truyện

- Dần dần, qua hành động nhân vật và phát hiện của nhân vật, không viết đoạn thuyết minh dài.
- Dùng đối thoại tự nhiên để truyền đạt thông tin cần thiết.
- Cho quy tắc thế giới hiện ra qua hành vi và hậu quả, không qua giảng giải.
- Bối cảnh phải là một phần chủ động của truyện: môi trường tạo chướng ngại và cơ hội, cho thấy nhân vật thích nghi hay vật lộn với thế giới của họ.
- Cân bằng sự kỳ lạ với sự tin được: neo yếu tố suy đoán vào trải nghiệm con người quen thuộc.

### Bước 8: Tuyến tình cảm (nếu có)

Áp dụng công thức **chướng ngại → tích tụ → bùng nổ**:
- **Chướng ngại**: dựng rào cản từ chính thế giới (cảnh giới chênh lệch, môn phái đối địch, thân phận, luật lệ), không tạo chướng ngại giả bằng hiểu lầm vô nghĩa.
- **Tích tụ**: để áp lực dồn dần qua nhiều chương, chi tiết nhỏ tích lại thành đủ để bùng.
- **Bùng nổ**: tới cao trào thì bung ra dứt khoát, trả nợ cảm xúc đã tích.

Danh sách cấm kỵ khi viết tình cảm gắn thế giới:
- Không tạo chướng ngại giả bằng hiểu lầm vô nghĩa có thể giải bằng một câu nói.
- Không để nhân vật vì tình mà đột ngột vô hiệu hóa quy tắc thế giới mình đã đặt.
- Không dồn tích tụ vô hạn, tích mãi không bùng thì độc giả bỏ.
- Không bùng nổ xong không trả nợ, cảnh cảm xúc rơi vào hư vô.

## Checklist kiểm tra

Trước khi lưu hồ sơ hoặc trước mỗi chương:

- [ ] Mỗi mục thế giới có nhãn duy nhất, mô tả, quy tắc, dòng thời gian liên quan.
- [ ] Thang cảnh giới có giới hạn trên và cái giá rõ ràng, không có lỗ hổng "vô địch vô hạn".
- [ ] Tiền tệ và tài nguyên khan hiếm có quy luật cung-cầu, không phải ATM rút ra là có.
- [ ] Bản đồ có khoảng cách và phạm vi thế lực, di chuyển tốn thời gian.
- [ ] Dòng thời gian lịch sử có phục bút, không có đại sự ký chết không dùng tới.
- [ ] Trạng thái thế giới đã cập nhật theo chương mới nhất.
- [ ] Hành vi nhân vật chương này có dính luật thế giới không?
- [ ] Xung đột chương mọc ra từ quy tắc, không phải chèn từ trên trời.
- [ ] Môi trường có vai trò với cảm xúc/chiến đấu chương này, không chỉ tả cảnh.
- [ ] Thiết lập lồng qua hành động và đối thoại, không có đoạn thuyết minh dài.
- [ ] Muốn sửa quy tắc thì đã sửa hồ sơ trước khi sửa bản thảo.
- [ ] Tuyến tình cảm có chướng ngại thật từ thế giới, có tích tụ, có điểm bùng.

## Lỗi thường gặp & cách sửa

| Lỗi | Cách sửa |
|---|---|
| Dùngto lớn thiết lập thay cho rắc rối trước mắt | Rắc rối trước mắt của nhân vật phải có trước; thiết lập chỉ phục vụ rắc rối đó |
| Dùng từ khóa chủ đề thay cho động cơ truyện | Viết rõ động cơ liên tục: 10-20 chương sau nhờ gì mà đi tiếp |
| Chônđiểm bán mạnh nhất sau đoạn giới thiệu dài | Đẩy bất thường, tương phản thân phận, khủng hoảng lên đầu |
| Đề nghị kéo dài một ý tưởng chỉ đủ cho một cú lật | Đánh giá lại: nếu không có động cơ liên tục thì chỉ nên viết ngắn |
| Chưa dựng khung tối thiểu đã vội viết chương | Dựng khung tối thiểu trước, xong mới mở bút |
| Thế giới hóa đá, không đổi trạng thái | Ghi trạng thái theo chương, cập nhật dòng thời gian |
| Nhân vật bay nhảy vô địch, bỏ qua luật đã đặt | Trước mỗi chương trả lời bốn câu hỏi thế giới |
| Đi tới nơi mà chương trước đã phá hủy hoặc chưa từng nhắc | Đối chiếu dòng trạng thái thế giới trước khi viết |
| Viết đoạn thuyết minh dài vềthiết lập | Lồng qua hành động, phát hiện, đối thoại của nhân vật |
| Thế giới quá phong phú thành bảo tàng | Nhắc lại: thế giới là móng nhà, phải phục vụ sảng điểm vàđọc theo dõi |
| Sửa quy tắc giữa chừng mà không sửa hồ sơ | Hồ sơ là nguồn sự thật duy nhất, sửa hồ sơ trước rồi mới sửa bản thảo |
| Tuyến tình cảm dùng hiểu lầm vô nghĩa làm chướng ngại | Chướng ngại phải từ quy tắc thế giới: cảnh giới, môn phái, thân phận |
| Tích tụ cảm xúc mãi không bùng | Đặt điểm bùng rõ, dồn đủ là bung, đừng để độc giả bỏ trước lúc đó |
