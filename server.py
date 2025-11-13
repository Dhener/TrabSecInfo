import socket
import ssl
import os
import threading
from typing import Optional


class FileTransferServer:
    """Servidor para recepção de arquivos com suporte a TCP e TLS"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5000, use_tls: bool = False):
        self.host = host
        self.port = port
        self.use_tls = use_tls
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.output_dir = "received_files"
        
        # Cria diretório para arquivos recebidos
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _create_socket(self) -> socket.socket:
        """Cria um socket TCP"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock
    
    def _setup_tls_context(self) -> ssl.SSLContext:
        """Configura contexto SSL/TLS"""
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Para desenvolvimento: gera certificado auto-assinado se não existir
        certfile = 'server.crt'
        keyfile = 'server.key'
        
        if not os.path.exists(certfile) or not os.path.exists(keyfile):
            print("[INFO] Gerando certificado auto-assinado...")
            self._generate_self_signed_cert(certfile, keyfile)
        
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        return context
    
    def _generate_self_signed_cert(self, certfile: str, keyfile: str):
        """Gera certificado auto-assinado usando OpenSSL"""
        cmd = (f'openssl req -new -x509 -days 365 -nodes -out {certfile} '
               f'-keyout {keyfile} -subj "/C=BR/ST=State/L=City/O=Organization/CN=localhost"')
        result = os.system(cmd)
        if result != 0:
            print("[AVISO] Não foi possível gerar certificado. Certifique-se de ter OpenSSL instalado.")
            print("No Linux/Mac: sudo apt-get install openssl ou brew install openssl")
            print("No Windows: Baixe de https://slproweb.com/products/Win32OpenSSL.html")
    
    def start(self):
        """Inicia o servidor"""
        try:
            # Cria socket base
            self.socket = self._create_socket()
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            protocol = "TLS" if self.use_tls else "TCP"
            print(f"[{protocol}] Servidor iniciado em {self.host}:{self.port}")
            print(f"[{protocol}] Aguardando conexões...")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    print(f"\n[{protocol}] Nova conexão de {address[0]}:{address[1]}")
                    
                    # Se usar TLS, envolve o socket
                    if self.use_tls:
                        context = self._setup_tls_context()
                        client_socket = context.wrap_socket(
                            client_socket,
                            server_side=True
                        )
                        print(f"[TLS] Handshake completado - Cipher: {client_socket.cipher()[0]}")
                    
                    # Cria thread para lidar com o cliente
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.start()
                    
                except KeyboardInterrupt:
                    print("\n[INFO] Encerrando servidor...")
                    break
                except Exception as e:
                    if self.running:
                        print(f"[ERRO] Erro ao aceitar conexão: {e}")
            
        except Exception as e:
            print(f"[ERRO] Falha ao iniciar servidor: {e}")
        finally:
            self.stop()
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Trata a comunicação com um cliente"""
        protocol = "TLS" if self.use_tls else "TCP"
        
        try:
            # Recebe os dados
            data = b""
            header_received = False
            filename = ""
            filesize = 0
            
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                
                data += chunk
                
                # Processa header na primeira recepção
                if not header_received and b"|" in data:
                    # Extrai header (filename|filesize|)
                    header_end = data.find(b"|", data.find(b"|") + 1) + 1
                    header = data[:header_end].decode('utf-8')
                    parts = header.split('|')
                    
                    if len(parts) >= 2:
                        filename = parts[0]
                        filesize = int(parts[1])
                        header_received = True
                        
                        # Remove header dos dados
                        data = data[header_end:]
                        
                        print(f"[{protocol}] Recebendo: {filename} ({filesize} bytes)")
                
                # Verifica se recebeu tudo
                if header_received and len(data) >= filesize:
                    break
            
            # Salva o arquivo
            if header_received:
                filepath = os.path.join(self.output_dir, f"{protocol}_{filename}")
                with open(filepath, 'wb') as f:
                    f.write(data[:filesize])
                
                print(f"[{protocol}] Arquivo salvo: {filepath}")
                
                # Envia confirmação
                client_socket.sendall(b"ACK: Arquivo recebido com sucesso!")
            
        except Exception as e:
            print(f"[{protocol}] Erro ao processar cliente: {e}")
        finally:
            client_socket.close()
            print(f"[{protocol}] Conexão encerrada com {address[0]}:{address[1]}")
    
    def stop(self):
        """Para o servidor"""
        self.running = False
        if self.socket:
            self.socket.close()


def start_tcp_server():
    """Inicia servidor TCP sem TLS na porta 5001"""
    server = FileTransferServer(port=5001, use_tls=False)
    server.start()


def start_tls_server():
    """Inicia servidor TLS na porta 5002"""
    server = FileTransferServer(port=5002, use_tls=True)
    server.start()


def main():
    """Função principal - inicia ambos os servidores"""
    print("="*60)
    print("SERVIDOR DE TRANSFERÊNCIA DE ARQUIVOS")
    print("="*60)
    print("1 - Servidor TCP (porta 5001)")
    print("2 - Servidor TLS (porta 5002)")
    print("3 - Ambos (recomendado para testes)")
    print("="*60)
    
    choice = input("\nEscolha uma opção: ").strip()
    
    if choice == "1":
        start_tcp_server()
    elif choice == "2":
        start_tls_server()
    elif choice == "3":
        # Inicia servidor TCP em thread separada
        tcp_thread = threading.Thread(target=start_tcp_server)
        tcp_thread.daemon = True
        tcp_thread.start()
        
        # Pequena pausa para garantir que TCP inicie primeiro
        import time
        time.sleep(1)
        
        # Inicia servidor TLS na thread principal
        start_tls_server()
    else:
        print("Opção inválida!")


if __name__ == "__main__":
    main()