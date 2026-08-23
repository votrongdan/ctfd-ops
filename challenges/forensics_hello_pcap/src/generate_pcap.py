import os
from scapy.all import Ether, IP, TCP, Raw, wrpcap

def build_pcap():
    flag = os.environ.get("FLAG", "flag{pcap_4nalys1s_w17h_w1r3sh4rk_f392a1}").strip()
    
    packets = []
    src_ip = "192.168.1.105"
    dst_ip = "10.0.0.42"
    src_port = 49152
    dst_port = 80
    
    # 1. TCP Handshake: SYN
    syn = Ether()/IP(src=src_ip, dst=dst_ip)/TCP(sport=src_port, dport=dst_port, flags="S", seq=1000)
    packets.append(syn)
    
    # 2. TCP SYN-ACK
    synack = Ether()/IP(src=dst_ip, dst=src_ip)/TCP(sport=dst_port, dport=src_port, flags="SA", seq=2000, ack=1001)
    packets.append(synack)
    
    # 3. TCP ACK
    ack = Ether()/IP(src=src_ip, dst=dst_ip)/TCP(sport=src_port, dport=dst_port, flags="A", seq=1001, ack=2001)
    packets.append(ack)
    
    # 4. HTTP GET Request
    http_req_payload = "GET /index.html HTTP/1.1\r\nHost: aegis-auth.internal\r\nUser-Agent: Mozilla/5.0\r\nAccept: */*\r\n\r\n"
    http_req = Ether()/IP(src=src_ip, dst=dst_ip)/TCP(sport=src_port, dport=dst_port, flags="PA", seq=1001, ack=2001)/Raw(load=http_req_payload)
    packets.append(http_req)
    
    # 5. HTTP GET Response
    http_resp_payload = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 45\r\n\r\n<html><body>Welcome to Aegis Internal</body></html>"
    http_resp = Ether()/IP(src=dst_ip, dst=src_ip)/TCP(sport=dst_port, dport=src_port, flags="PA", seq=2001, ack=1001 + len(http_req_payload))/Raw(load=http_resp_payload)
    packets.append(http_resp)

    # 6. HTTP POST Auth Request with Flag
    src_port2 = 49154
    http_post_payload = (
        "POST /api/v1/authenticate HTTP/1.1\r\n"
        "Host: aegis-auth.internal\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(flag) + 40}\r\n\r\n"
        f'{{"username":"admin","secret_flag":"{flag}"}}'
    )
    http_post = Ether()/IP(src=src_ip, dst=dst_ip)/TCP(sport=src_port2, dport=dst_port, flags="PA", seq=3000, ack=4000)/Raw(load=http_post_payload)
    packets.append(http_post)
    
    # 7. HTTP POST Auth Response
    auth_resp_payload = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"status\":\"authenticated\",\"message\":\"Flag accepted!\"}"
    auth_resp = Ether()/IP(src=dst_ip, dst=src_ip)/TCP(sport=dst_port, dport=src_port2, flags="PA", seq=4000, ack=3000 + len(http_post_payload))/Raw(load=auth_resp_payload)
    packets.append(auth_resp)
    
    out_path = os.path.join(os.path.dirname(__file__), "evidence.pcap")
    wrpcap(out_path, packets)
    print(f"Generated PCAP at {out_path}")

if __name__ == "__main__":
    build_pcap()
