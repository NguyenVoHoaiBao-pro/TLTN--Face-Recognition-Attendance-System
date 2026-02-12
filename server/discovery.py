import socket

def start_discovery():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 37020))

    print("[DISCOVERY] UDP listening on port 37020")

    while True:
        data, addr = sock.recvfrom(1024)
        if data == b"DISCOVER_ATTENDANCE_SERVER":
            sock.sendto(b"ATTENDANCE_SERVER_OK", addr)
