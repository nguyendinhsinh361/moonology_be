Tôi thấy bạn đã vào tab **Exec** và đang ở thư mục `/data` với file `dump.rdb` (Redis database file). Bây giờ để truy vấy dữ liệu Redis, bạn cần:

## 1. Khởi động Redis CLI

Gõ lệnh sau trong terminal:

```bash
redis-cli
```

## 2. Sau khi vào Redis CLI, bạn sẽ thấy prompt như:

```
127.0.0.1:6379>
```

## 3. Các lệnh cơ bản để khám phá dữ liệu:

**Kiểm tra kết nối:**

```bash
PING
```

**Xem tất cả keys:**

```bash
KEYS *
```

**Xem thông tin database:**

```bash
INFO keyspace
```

**Đếm số lượng keys:**

```bash
DBSIZE
```

**Xem loại dữ liệu của một key:**

```bash
TYPE key_name
```

**Lấy dữ liệu:**

```bash
GET key_name              # Cho string
HGETALL key_name          # Cho hash
LRANGE key_name 0 -1      # Cho list
SMEMBERS key_name         # Cho set
ZRANGE key_name 0 -1      # Cho sorted set
```

## 4. Nếu muốn thoát Redis CLI:

```bash
EXIT
```

Hãy thử gõ `redis-cli` trước, sau đó dùng `KEYS *` để xem có dữ liệu gì trong Redis không nhé!
