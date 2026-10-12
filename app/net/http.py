# 아주 작은 HTTPS GET — 리디렉션을 따라가고, 응답 본문을 바로 파일로 저장 (RAM 절약)
#
# Apps Script 웹 앱은 script.google.com → script.googleusercontent.com 으로 302 리디렉션한다.
# HTTP/1.0 으로 요청해서 보통은 chunked 응답이 오지 않지만, 혹시 오면 풀어서 저장한다.
# (인증서 검증은 하지 않음: Pico 에 CA 목록이 없음. 주소의 token 이 비밀번호 역할)
import socket
import ssl


def _split(url):
    proto, _, rest = url.partition("://")
    host, _, path = rest.partition("/")
    port = 443 if proto == "https" else 80
    if ":" in host:
        host, p = host.split(":", 1)
        port = int(p)
    return proto, host, port, "/" + path


def get_to_file(url, path, timeout=20, max_redirects=5):
    """url 을 받아 path 에 저장. 저장한 바이트 수를 돌려줌. 실패하면 OSError."""
    for _ in range(max_redirects + 1):
        proto, host, port, rpath = _split(url)
        ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)[0]
        s = socket.socket(ai[0], ai[1], ai[2])
        s.settimeout(timeout)
        stage = "연결"
        try:
            s.connect(ai[-1])
            if proto == "https":
                stage = "TLS"
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.verify_mode = ssl.CERT_NONE
                s = ctx.wrap_socket(s, server_hostname=host)
            stage = "요청 보내기"
            req = ("GET %s HTTP/1.0\r\nHost: %s\r\nUser-Agent: epaper-calendar\r\n"
                   "Connection: close\r\n\r\n") % (rpath, host)
            s.write(req.encode())

            stage = "응답 기다리기"
            status_line = s.readline()
            parts = status_line.split(None, 2)
            if len(parts) < 2:
                raise OSError("HTTP 응답이 이상함: %r" % status_line)
            status = int(parts[1])
            location = None
            chunked = False
            while True:
                line = s.readline()
                if not line or line == b"\r\n":
                    break
                low = line.lower()
                if low.startswith(b"location:"):
                    location = line[9:].strip().decode()
                elif low.startswith(b"transfer-encoding:") and b"chunked" in low:
                    chunked = True

            if status in (301, 302, 303, 307, 308) and location:
                if location.startswith("/"):
                    location = "%s://%s%s" % (proto, host, location)
                url = location
                continue
            if status != 200:
                raise OSError("HTTP %d" % status)

            stage = "본문 받기"
            n = 0
            buf = bytearray(1024)
            mv = memoryview(buf)
            with open(path, "wb") as f:
                if chunked:
                    while True:
                        size = int(s.readline().split(b";")[0].strip() or b"0", 16)
                        if size == 0:
                            break
                        while size:
                            k = s.readinto(mv[:min(size, len(buf))])
                            if not k:
                                raise OSError("응답이 중간에 끊김")
                            f.write(mv[:k])
                            n += k
                            size -= k
                        s.readline()                 # 청크 끝의 \r\n
                else:
                    while True:
                        k = s.readinto(buf)
                        if not k:
                            break
                        f.write(mv[:k])
                        n += k
            return n
        except OSError as e:
            raise OSError("%s (%s 중, %s)" % (e, stage, host))
        finally:
            s.close()
    raise OSError("리디렉션이 너무 많음")
