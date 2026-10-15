# anti-ai-prose

```yaml
name: anti-ai-prose
description: Dùng khi bản dịch/convert đọc lên thấy "giống văn AI" (tạp văn, sáo ngữ, một giọng, kết chương kiểu tổng kết) để chẩn đoán và sửa ở tầng mặt chữ, đối thoại, nhịp câu.
```

## Mục đích

Chống "văn AI" ở tầng mặt chữ: câu sáo, phán đoán trừu tượng, một giọng nói cho mọi nhân vật, nhịp câu đều tăm tắp, kết chương kiểu tổng kết. Bổ trợ `/skill:novel-deslop`: skill đó lo cấu trúc, logic, mạch truyện; skill này lo lớp ngôn ngữ sau khi cấu trúc đã ổn.

## Khi nào dùng

- Bản dịch/convert có: phán đoán trống ("nàng rất đau lòng", "không khí hơi vi diệu"), sáo ngữ ("giống như", "phảng phất", "không kìm được"), một giọng nói cho tất cả, câu dài ngắn đều nhau, kết chương kiểu "hắn rốt cuộc hiểu ra...".
- Sửa chủ yếu ở tầng mặt chữ, không phải ở đại cương hay nhân quả.
- Nếu truyện vỡ ở tầng dưới (nhân quả đứt, động cơ không đứng, chuyển cảnh gãy, nhân vậttrước sau mâu thuẫn), sửa tầng dưới trước rồi mới quay lại dùng skill này.

## Quy trình

**Bước 1: Chẩn đoán tầng lỗi.** Xác định lỗi chính thuộc tầng nào, không sửa lan man cả đoạn:

1. Tầng phán đoán trống: toàn câu kết luận, không có hiện trường. Sửa bằng hành động, vật cụ, chuỗi phản ứng.
2. Tầng một giọng: ai cũng giải thích trọn vẹn, lịch sự, nhã nhặn; không còn chênh lệch thân phận, lập trường, cách ép người. Sửa bằng chênh lệch thân phận, chênh lệch lập trường, chênh lệch cách áp chế.
3. Tầng sáo ngữ bao trùm: "không khí như đông cứng", "thời gian như ngừng trôi". Sửa bằng biến đổi trong sân, tiếng nhỏ nghe được, thay đổi khoảng cách và động tác.
4. Tầng nhịp đều: câu dài ngắn na ná, cảm xúc càng lớn càng viết trọn, không ngắt câu, không ngập ngừng, không bị cắt ngang. Sửa bằng kéo giãn độ dài câu, cắt ngang bằng động tác, đâm bằng câu ngắn.

**Bước 2: Lập kế hoạch thay thế trước khi sửa.** Trả lời sáu câu: câu trống nhất đoạn này là gì; định xóa hay tách nó; cảm xúc này hợp rơi vào động tác hay vật cụ nào; ai trong đoạn này cần nói một câu mang thân phận; câu nào cần rút ngắn hoặc bị cắt ngang; sau khi sửa, cục diện có ép hơn không. Nếu không trả lời được, chưa vội đánh bóng.

**Bước 3: Sửa theo thứ tự.** Xóa câu phán đoán trừu tượng trước; đánh dấu chỗ có thể rơi vào vật cụ, động tác, ngắt quãng; tìm câu thoại không giống người nói; rồi mới quyết định thứ tự thay thế. Nguyên tắc cứng: dùng hành động thay tổng kết, dùng thoại thay giải thích, dùng cụ thể thay trừu tượng, dùng thân phận thay một giọng, sửa cục diện chứ không chỉ sửa mặt chữ, chỗ ngắn được thì đừng kéo dài, chỗ dừng được thì đừng nói hết. Chống văn AI không phải là cố ý viết thô.

**Bước 4: Ba lượt hệ thống** (khi sửa cả chương):

- Lượt 1, trừu tượng hóa: xóa câu tổng kết cảm xúc, câu giả sâu, câu kết luận trống, câu so sánh quá ngay ngắn; giảm một nửa tính từ trang trí; chia giọng nói khác nhau cho các nhân vật.
- Lượt 2, bỏ văn vẻ: từ phân tích ("cơ chế", "kết cấu", "hệ thống") đổi sang lời thường; từ trừu tượng nói thẳng việc; bỏ từ ngữ công văn. Ngoại lệ: cảnh cần giữ trang trọng (lịch sử, văn học cố ý, hài khoa trương).
- Lượt 3, trả lại tự nhiên: thêm một hai chi tiết cảm quan; phân biệt giọng nói theo vị trí xã hội; đổi cách mở câu khi ba câu liên tiếp cùng chủ ngữ; xen kẽ dài ngắn theo nhịp cảm xúc, không phải ngẫu nhiên.

**Bước 5: Tuyến tình cảm** áp dụng công thức chướng ngại → tích tụ → bùng nổ: chướng ngại cụ thể (không phải "họ gặp khó khăn"), tích tụ qua hành động và ngắt quãng (không phải lời tự sự dài), bùng nổ bằng hành động và thoại ngắn. Danh sách cấm kỵ: tổng kết cảm xúc thay cho diễn biến; giải thích động cơ trọn vẹn; mọi thứ khép kín sạch sẽ; xung đột "hiểu lầm rồi giải thích rồi xong" mà không bám thêm; cảm xúc trung bình cho tất cả nhân vật.

## Checklist kiểm tra

- [ ] Câu nào xóa đi đoạn gần như không đổi thì đó là câu tổng kết trống.
- [ ] Ba câu phán đoán liên tiếp không có câu nào rơi vào hành động.
- [ ] Nhân vật trong cảnh áp lực nói câu quá trọn vẹn, quá lý lẽ.
- [ ] Một đoạn dồn nhiều tính từ cùng loại.
- [ ] Có câu kiểu "không khí hơi vi diệu" (tác giả thay độc giả kết luận).
- [ ] Sau khi sửa, độc giả không cần lời giải thích cũng biết ai sợ ai, ai nhường ai, ai đang cố gồng.
- [ ] Thoại có phân biệt được người nói không, không phải một giọng.
- [ ] Kết chương là móc câu (hành động, thoại,nghi vấn), không phải tổng kết, không phải thăng hoa, không phải "hắn không biết rằng...".
- [ ] Không có trang trí ký hiệu (✦ ✨ ◆ ● ▪ ★); phân cảnh dùng dòng trống.
- [ ] Đoạn đọc như cương yếu (điện báo) thì đã gọt quá tay: trả lại từ nối tự nhiên cho câu không phải điểm nhấn.

## Lỗi thường gặp & cách sửa

| Lỗi | Cách sửa |
|---|---|
| Tổng kết cảm xúc ("nàng thập phần bi ai") | Xóa; hỏi "cơ thể cô ấy xảy ra gì trước"; tìm một động tác hoặc vật cụ đỡ lấy |
| Sáo ngữ bao trùm ("không khí như đông cứng") | Viết ai im, ai lùi một bước, âm thanh nào bỗng chói tai |
| Đống tính từ ("lạnh lùng, nguy hiểm, thâm trầm, từ tính") | Bỏ hơn một nửa, giữ một hai cảm giác trọng yếu, thêm một động tác gây áp lực |
| Thoại kiểu hướng dẫn ("thực ra ta làm vậy là vì...") | Đổi sang lập trường, điều kiện, hậu quả, thông điệp cuối |
| Nhịp đều, câu dài ngắn na ná | Câu ngắn đâm vào, động tác cắt ngang, để một câu nói dở dang |
| "Không phải A, mà là B" | Viết thẳng B |
| ", mang theo..." làm trạng ngữ vạn năng | Bỏ trạng ngữ, giữ chủ ngữ, hoặc đổi sang động tác cụ thể |
| "Trong mắt lóe qua một tia...", "trên miệng nhếch lên một nụ..." | Đổi thành hạ mắt, giật mép |
| "Trong lòng dâng lên một cỗ...", "tim giật nảy" | Đổi thành phản ứng thân thể |
| Diễn giải nhân quả ("bởi vì...", "hóa ra...", "điều này có nghĩa là...") | Xóa; để nhân quả lộ ra qua hành động, thoại, phản ứng |
| Nhìn thấu bao quát ("nàng không biết rằng...", "hóa ra...") | Xóa; chỉ viết nhân vật biết lúc này |
| Kết chương thăng hoa ("đêm nay, định không ai ngủ được") | Kết bằng một động tác hoặc một câu bỏ ngỏ |
| Trùng lặp (cùng một ẩn dụ, cùng một cấu trúc, cùng một từ) | Giữ lần đầu, xóa các lần sau; mỗi chỗ dùng cách viết khác nhau |
| Đồng nghĩa nói đi nói lại ("hắn rất tức giận, hắn nổi giận, lửa giận bùng lên") | Giữ một chỗ chính xác nhất, tốt nhất đổi thành hành động |
| Từ cực đoan ("rất rất lớn") | Đổi thành hình ảnh cụ thể |
| Câu cảm thăng vô cớ ("cuộc sống luôn đầy thử thách") | Xóa |
| Chấm thành dấu phẩy ("Hắn mua táo. Chuối. Cam.") | Liệt kê dùng dấu phẩy, nửa câu dùng dấu phẩy, chấm để lại cho câu trọn |
| Đốidựa vào quá ngay ngắn, đoạn trên dưới bằng nhau | Xen kẽ dài ngắn, phá đối xứng |
| Dấu ngoặc kép nhọn 「」『』 hoặc thẳng " " | Thay bằng ngoặc kép cong "" |
| Dấu gạch dài , ,  lạm dụng | Một chương tối đa một lần; nếu không có chức năng thì bỏ |
| Ba phép tu từ liên tiếp | Cắt còn một phép mạnh nhất |
| Trích dẫn lệch ngữ điệu (thơ cổ, triết học, meme hiện đại chen vào truyện đời thường) | Bỏ hoặc đổi; nhất quán ngữ điệu > một câu đơn lẻ hay |
| Điện báo (mọi câu đều ngắn, đọc như cương yếu) | Trả lại từ nối và câu trung dài cho câu không phải điểm nhấn; điểm nhấn vẫn giữ ngắn |
| Đảo ngược trơn tru ("tay cầm đao, hắn xông lên") | Đổi chủ ngữ mở đầu bằng vật cụ, âm thanh, phản hồi môi trường |
| Liệt kê động tác như camera giám sát | Gộp động vụn, chỉ giữ động tác có chức năng cảm xúc/tình tiết/không gian |
| Tăng tỷ lệ thoại cưỡng bức | Chỉ thêm khi nhân vật thật sự nói và buộc phải nói lúc này |

## Luật nhà

- Thoại luôn trong ngoặc kép thẳng "..."; tuyệt đối không dùng dấu gạch dài (, ) ở bất cứ đâu.
- Tu sĩ không bao giờ xưng "tôi"; chỉ phàm nhân xưng "tôi". Tu sĩ nói với phàm nhân: bản tọa / lão phu (hoặc bản công tử, bổn cô nương theo thân phận). Đồng cấp: tại hạ ↔ đạo hữu. Tông môn: vãn bối/đệ tử/sư huynh/sư đệ/tiền bối.
- Độ dài chương bám mục tiêu của bộ ±15%; mọi chương kết bằng móc câu (hook).
