import socket
import ssl
import os
import time
from typing import Optional, Tuple


class FileTransferClient:
    """Cliente para transferência de arquivos com suporte a TCP e TLS"""
    
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.transfer_stats = {
            'bytes_sent': 0,
            'transfer_time': 0.0,
            'packet_overhead': 0
        }
    
    def _create_socket(self) -> socket.socket:
        """Cria um socket TCP"""
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect_plain(self) -> bool:
        """Estabelece conexão TCP sem criptografia"""
        try:
            self.socket = self._create_socket()
            print(f"[TCP] Conectando a {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            print("[TCP] Conexão estabelecida com sucesso!")
            return True
        except Exception as e:
            print(f"[ERRO] Falha na conexão TCP: {e}")
            return False
    
    def connect_tls(self, certfile: Optional[str] = None) -> bool:
        """Estabelece conexão TCP com TLS"""
        try:
            # Cria socket base
            base_socket = self._create_socket()
            
            # Configura contexto SSL/TLS
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            
            # Para ambiente de desenvolvimento (aceita certificados auto-assinados)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Envolve o socket com TLS
            self.socket = context.wrap_socket(
                base_socket,
                server_hostname=self.host
            )
            
            print(f"[TLS] Conectando a {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            
            # Exibe informações da conexão TLS
            cipher = self.socket.cipher()
            version = self.socket.version()
            print(f"[TLS] Conexão estabelecida com sucesso!")
            print(f"[TLS] Protocolo: {version}")
            print(f"[TLS] Cipher: {cipher[0]}")
            
            return True
        except Exception as e:
            print(f"[ERRO] Falha na conexão TLS: {e}")
            return False
    
    def send_file(self, filepath: str) -> bool:
        """Envia arquivo através da conexão estabelecida"""
        if not self.socket:
            print("[ERRO] Nenhuma conexão estabelecida!")
            return False
        
        if not os.path.exists(filepath):
            print(f"[ERRO] Arquivo não encontrado: {filepath}")
            return False
        
        try:
            # Lê o conteúdo do arquivo
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Prepara os dados para envio
            filename = os.path.basename(filepath)
            filesize = len(content.encode('utf-8'))
            
            print(f"\n[INFO] Enviando arquivo: {filename}")
            print(f"[INFO] Tamanho: {filesize} bytes")
            
            # Envia metadados (nome e tamanho)
            header = f"{filename}|{filesize}|".encode('utf-8')
            
            # Marca tempo inicial
            start_time = time.time()
            
            # Envia header
            self.socket.sendall(header)
            
            # Envia conteúdo
            self.socket.sendall(content.encode('utf-8'))
            
            # Marca tempo final
            end_time = time.time()
            
            # Aguarda confirmação
            ack = self.socket.recv(1024).decode('utf-8')
            
            # Calcula estatísticas
            self.transfer_stats['bytes_sent'] = len(header) + filesize
            self.transfer_stats['transfer_time'] = end_time - start_time
            
            print(f"[OK] Arquivo enviado com sucesso!")
            print(f"[INFO] Tempo de transferência: {self.transfer_stats['transfer_time']:.4f}s")
            print(f"[INFO] Resposta do servidor: {ack}")
            
            return True
            
        except Exception as e:
            print(f"[ERRO] Falha no envio: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Retorna estatísticas da transferência"""
        return self.transfer_stats.copy()
    
    def close(self):
        """Fecha a conexão"""
        if self.socket:
            self.socket.close()
            print("[INFO] Conexão fechada.")


def main():
    """Função principal para demonstração"""
    
    # Cria arquivo de teste
    test_file = "teste.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Este é um arquivo de teste para transferência.\n" * 100)
    
    print("="*60)
    print("TESTE 1: Transferência sem TLS (TCP Puro)")
    print("="*60)
    
    # Cliente TCP sem TLS
    client_plain = FileTransferClient(host='localhost', port=5001)
    if client_plain.connect_plain():
        client_plain.send_file(test_file)
        stats_plain = client_plain.get_stats()
        client_plain.close()
    
    print("\n" + "="*60)
    print("TESTE 2: Transferência com TLS")
    print("="*60)
    
    # Cliente TCP com TLS
    client_tls = FileTransferClient(host='localhost', port=5002)
    if client_tls.connect_tls():
        client_tls.send_file(test_file)
        stats_tls = client_tls.get_stats()
        client_tls.close()
    
    # Comparação
    print("\n" + "="*60)
    print("COMPARAÇÃO DE DESEMPENHO")
    print("="*60)
    print(f"TCP Puro  - Bytes: {stats_plain['bytes_sent']}, Tempo: {stats_plain['transfer_time']:.4f}s")
    print(f"TCP + TLS - Bytes: {stats_tls['bytes_sent']}, Tempo: {stats_tls['transfer_time']:.4f}s")
    print(f"Overhead de tempo: {((stats_tls['transfer_time'] - stats_plain['transfer_time']) / stats_plain['transfer_time'] * 100):.2f}%")


if __name__ == "__main__":
    main()