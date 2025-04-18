import os
import base64
import hashlib
import uuid

def generate_auth_params():
    # 1. 生成 code_verifier (t) - 32字节随机数
    t = os.urandom(32)  # 等效于 JS 的 crypto.getRandomValues(new Uint8Array(32))

    # 2. 生成 s: 对 t 进行 Base64 URL 安全编码
    def tb(data):
        # Base64 URL 安全编码（替换 +/ 为 -_，去除末尾的 =）
        return base64.urlsafe_b64encode(data).decode().rstrip('=')
    
    s = tb(t)  # 对应 JS 的 this.tb(t)

    # 3. 生成 n: 对 s 进行 SHA-256 哈希 + Base64 URL 编码
    def ub(s_str):
        # 等效于 JS 的 TextEncoder().encode(s) + SHA-256
        return hashlib.sha256(s_str.encode()).digest()
    
    hashed = ub(s)
    n = tb(hashed)  # 对应 JS 的 this.tb(new Uint8Array(hashed))

    # 4. 生成 r: UUID v4
    r = str(uuid.uuid4())  # 对应 JS 的 $t()

    return {
        "t": t.hex(),      # 原始字节转十六进制字符串（方便查看）
        "s": s,
        "n": n,
        "r": r
    }

print(generate_auth_params())