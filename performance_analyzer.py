import time
import statistics
from typing import List, Dict
import json


class PerformanceAnalyzer:
    """Classe para análise de desempenho de transferências TCP vs TLS"""
    
    def __init__(self):
        self.results: Dict[str, List[Dict]] = {
            'tcp': [],
            'tls': []
        }
    
    def add_result(self, protocol: str, bytes_sent: int, transfer_time: float, 
                   file_size: int, overhead: int = 0):
        """Adiciona resultado de uma transferência"""
        result = {
            'bytes_sent': bytes_sent,
            'transfer_time': transfer_time,
            'file_size': file_size,
            'overhead': overhead,
            'throughput': bytes_sent / transfer_time if transfer_time > 0 else 0
        }
        self.results[protocol.lower()].append(result)
    
    def calculate_statistics(self, protocol: str) -> Dict:
        """Calcula estatísticas para um protocolo"""
        if not self.results[protocol]:
            return {}
        
        times = [r['transfer_time'] for r in self.results[protocol]]
        throughputs = [r['throughput'] for r in self.results[protocol]]
        overheads = [r['overhead'] for r in self.results[protocol]]
        
        return {
            'count': len(times),
            'avg_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'stdev_time': statistics.stdev(times) if len(times) > 1 else 0,
            'avg_throughput': statistics.mean(throughputs),
            'avg_overhead': statistics.mean(overheads) if overheads else 0
        }
    
    def compare_protocols(self) -> Dict:
        """Compara desempenho entre TCP e TLS"""
        tcp_stats = self.calculate_statistics('tcp')
        tls_stats = self.calculate_statistics('tls')
        
        if not tcp_stats or not tls_stats:
            return {}
        
        time_overhead = ((tls_stats['avg_time'] - tcp_stats['avg_time']) / 
                        tcp_stats['avg_time'] * 100)
        
        throughput_reduction = ((tcp_stats['avg_throughput'] - tls_stats['avg_throughput']) / 
                               tcp_stats['avg_throughput'] * 100)
        
        return {
            'tcp': tcp_stats,
            'tls': tls_stats,
            'time_overhead_percent': time_overhead,
            'throughput_reduction_percent': throughput_reduction,
            'tls_slowdown_factor': tls_stats['avg_time'] / tcp_stats['avg_time']
        }
    
    def generate_report(self, filename: str = 'performance_report.txt'):
        """Gera relatório detalhado"""
        comparison = self.compare_protocols()
        
        if not comparison:
            print("Dados insuficientes para gerar relatório")
            return
        
        report = []
        report.append("="*70)
        report.append("RELATÓRIO DE ANÁLISE DE DESEMPENHO: TCP vs TLS")
        report.append("="*70)
        report.append("")
        
        # Estatísticas TCP
        report.append("PROTOCOLO TCP (sem criptografia)")
        report.append("-"*70)
        tcp = comparison['tcp']
        report.append(f"  Número de testes: {tcp['count']}")
        report.append(f"  Tempo médio: {tcp['avg_time']:.6f}s")
        report.append(f"  Tempo mínimo: {tcp['min_time']:.6f}s")
        report.append(f"  Tempo máximo: {tcp['max_time']:.6f}s")
        report.append(f"  Desvio padrão: {tcp['stdev_time']:.6f}s")
        report.append(f"  Throughput médio: {tcp['avg_throughput']:.2f} bytes/s")
        report.append("")
        
        # Estatísticas TLS
        report.append("PROTOCOLO TLS (com criptografia)")
        report.append("-"*70)
        tls = comparison['tls']
        report.append(f"  Número de testes: {tls['count']}")
        report.append(f"  Tempo médio: {tls['avg_time']:.6f}s")
        report.append(f"  Tempo mínimo: {tls['min_time']:.6f}s")
        report.append(f"  Tempo máximo: {tls['max_time']:.6f}s")
        report.append(f"  Desvio padrão: {tls['stdev_time']:.6f}s")
        report.append(f"  Throughput médio: {tls['avg_throughput']:.2f} bytes/s")
        report.append(f"  Overhead médio: {tls['avg_overhead']:.2f} bytes")
        report.append("")
        
        # Comparação
        report.append("ANÁLISE COMPARATIVA")
        report.append("-"*70)
        report.append(f"  Overhead de tempo (TLS vs TCP): {comparison['time_overhead_percent']:.2f}%")
        report.append(f"  Redução de throughput: {comparison['throughput_reduction_percent']:.2f}%")
        report.append(f"  Fator de desaceleração: {comparison['tls_slowdown_factor']:.2f}x")
        report.append("")
        
        report.append("INTERPRETAÇÃO DOS RESULTADOS")
        report.append("-"*70)
        report.append(f"  O TLS adiciona aproximadamente {comparison['time_overhead_percent']:.1f}% de")
        report.append(f"  overhead temporal devido ao:")
        report.append(f"    - Handshake inicial (negociação de cifras)")
        report.append(f"    - Criptografia/descriptografia dos dados")
        report.append(f"    - Verificação de integridade (MAC)")
        report.append("")
        report.append(f"  Este overhead é o preço da segurança, garantindo:")
        report.append(f"    - Confidencialidade (dados não podem ser lidos)")
        report.append(f"    - Integridade (dados não podem ser modificados)")
        report.append(f"    - Autenticidade (verificação da identidade do servidor)")
        report.append("")
        report.append("="*70)
        
        # Salva em arquivo
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        # Exibe na tela
        print('\n'.join(report))
        print(f"\nRelatório salvo em: {filename}")
        
        # Salva dados brutos em JSON
        json_filename = filename.replace('.txt', '.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2)
        print(f"Dados brutos salvos em: {json_filename}")
    
    def export_csv(self, filename: str = 'performance_data.csv'):
        """Exporta dados para CSV"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("protocol,test_number,bytes_sent,transfer_time,file_size,overhead,throughput\n")
            
            for protocol in ['tcp', 'tls']:
                for i, result in enumerate(self.results[protocol], 1):
                    f.write(f"{protocol},{i},{result['bytes_sent']},"
                           f"{result['transfer_time']:.6f},{result['file_size']},"
                           f"{result['overhead']},{result['throughput']:.2f}\n")
        
        print(f"Dados exportados para: {filename}")


# Exemplo de uso
def run_performance_tests():
    """Executa testes de desempenho"""
    from client import FileTransferClient
    import os
    
    analyzer = PerformanceAnalyzer()
    
    # Cria arquivo de teste
    test_file = "teste_performance.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Dados de teste para análise de desempenho.\n" * 1000)
    
    file_size = os.path.getsize(test_file)
    num_tests = 10
    
    print("Iniciando testes de desempenho...")
    print(f"Arquivo de teste: {test_file} ({file_size} bytes)")
    print(f"Número de testes por protocolo: {num_tests}\n")
    
    # Testa TCP
    print("Testando TCP...")
    for i in range(num_tests):
        client = FileTransferClient(port=5001)
        if client.connect_plain():
            client.send_file(test_file)
            stats = client.get_stats()
            analyzer.add_result('tcp', stats['bytes_sent'], 
                              stats['transfer_time'], file_size)
            client.close()
        time.sleep(0.1)
    
    # Testa TLS
    print("\nTestando TLS...")
    for i in range(num_tests):
        client = FileTransferClient(port=5002)
        if client.connect_tls():
            client.send_file(test_file)
            stats = client.get_stats()
            analyzer.add_result('tls', stats['bytes_sent'], 
                              stats['transfer_time'], file_size, 
                              overhead=stats['bytes_sent'] - file_size)
            client.close()
        time.sleep(0.1)
    
    # Gera relatórios
    print("\n" + "="*70)
    analyzer.generate_report()
    analyzer.export_csv()


if __name__ == "__main__":
    run_performance_tests()