# FuCache

[![GitHub license](https://img.shields.io/badge/license-BSD_3--Clause-green.svg)](https://github.com/futa-t/fucache/blob/main/LICENSE)

## Simple Cache System
最低限のキャッシュ機能を提供するやつ

## 使い方
```python
from fucache import FuCache

# 初期化
FuCache.init("MyApp")
data = "nanka hozon sitai data"

# 保存(有効期限なし)
FuCache.save_cache("hozon.txt", data.encode())
if load_data := FuCache.load_cache("hozon.txt"):
    print(load_data.decode())

# キャッシュ全消去
FuCache.clean_all()

# 保存(有効期限あり。10秒)
import time

FuCache.init("MyApp", expiration_sec=10)

data = "nanka 10byo de kieru data"

FuCache.save_cache("hozon.txt", data.encode())

time.sleep(11)
if load_data := FuCache.load_cache("hozon.txt"):
    print(load_data.decode())
else:
    print("No Cache")

# 期限切れキャッシュ全消去
FuCache.clean_expired()

```
## TODO
- キャッシュディレクトリのサイズ制限
- 暗号化