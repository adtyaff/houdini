import requests
from bs4 import BeautifulSoup
import pyfiglet
import random
import time
import socket
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor, as_completed

console = Console()

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0"
]

def show_logo():
    logo_text = pyfiglet.figlet_format("iNHUMaN", font="slant")
    logo_width = max([len(line) for line in logo_text.split("\n")])
    
    console.print(f"[bold white]{'-' * logo_width}[/bold white]")
    console.print(f"[bold white]{logo_text}[/bold white]")
    
    houdini_text = "HOUDINI 1.0"
    padding = (logo_width - len(houdini_text)) // 2
    console.print(f"[bold white]{' ' * padding}{houdini_text}[/bold white]")
    console.print(f"[bold white]{'-' * logo_width}[/bold white]")

def handle_rate_limiting(retry_count):
    wait_time = 2 ** retry_count
    console.print(f"[bold yellow]Tunggu sebentar {wait_time} detik karena terlalu banyak permintaan.[/bold yellow]")
    time.sleep(wait_time)

def reverse_ip_genz(ip, session, retry_count=0):
    url = f"https://rapiddns.io/sameip/{ip}?full=1&t=None#result"
    headers = {"User-Agent": random.choice(user_agents)}
    
    try:
        response = session.get(url, headers=headers)
        
        if response.status_code == 429:
            handle_rate_limiting(retry_count)
            if retry_count < 5:
                return reverse_ip_genz(ip, session, retry_count + 1)
            else:
                console.print(f"[bold red]IP {ip} terlalu banyak permintaan, coba lagi nanti.[/bold red]")
                return None

        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'table table-striped table-bordered'})
        if not table:
            return None

        rows = table.find('tbody').find_all('tr') if table else []
        
        domains = []
        for row in rows:
            columns = row.find_all('td')
            if len(columns) > 0:
                domain_name = columns[0].text.strip()
                if domain_name:
                    domains.append(domain_name)
        
        return domains if domains else None
    except Exception as e:
        console.print(f"[bold red]Terjadi kesalahan saat memproses IP {ip}: {e}[/bold red]")
        return None

def process_ip(ip, session, result_file):
    time.sleep(random.uniform(1, 3))
    
    domain_list = reverse_ip_genz(ip, session)
    if domain_list:
        total_domains = len(domain_list)
        with open(result_file, 'a') as hasil_file:
            for domain in domain_list:
                hasil_file.write(f"{domain}\n")
        console.print(f"[bold white]🔍 Memeriksa IP [/bold white][bold green]{ip}[/bold green] [bold yellow]=> Ditemukan {total_domains} domain[/bold yellow]")
    else:
        console.print(f"[bold white]🔍 Memeriksa IP [/bold white][bold green]{ip}[/bold green] [bold red]=> Tidak ada domain yang ditemukan![/bold red]")

def cek_domain_threaded(ip_list, result_file, num_threads):
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(process_ip, ip, session, result_file) for ip in ip_list]
            for future in as_completed(futures):
                future.result()

def baca_list(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Main function
def main():
    show_logo()
    console.print("[bold white]Pilih menu berikut:[/bold white]")
    
    console.print("[bold green]Ketik 'domip' untuk cek Domain ke IP[/bold green]")
    console.print("[bold green]Ketik 'revip' untuk Reverse IP Lookup[/bold green]")
    
    choice = console.input("[bold white]Masukkan pilihan: [/bold white]").strip().lower()

    if choice == 'domip':
        file_path = console.input("[bold green]Masukkan file berisi list domain (contoh: domain_list.txt): [/bold green]")
        result_file = console.input("[bold green]Nama file hasil IP (contoh: ip_result.txt): [/bold green]")
        
        domain_list = baca_list(file_path)
        
        with open(result_file, 'a') as result:
            for domain in domain_list:
                try:
                    ip = socket.gethostbyname(domain)
                    result.write(f"{domain} => {ip}\n")
                    console.print(f"[bold white]🔁 Domain [/bold white][bold yellow]{domain}[/bold yellow] [bold white]=> IP: {ip}[/bold white]")
                except socket.gaierror:
                    console.print(f"[bold white]🔁 Domain [/bold white][bold yellow]{domain}[/bold yellow] [bold red]=> IP tidak ditemukan![/bold red]")

    elif choice == 'revip':
        file_path = console.input("[bold green]Masukkan file berisi list IP (contoh: list_ip.txt): [/bold green]")
        result_file = console.input("[bold green]Nama file hasil (contoh: domain1.txt): [/bold green]")
        
        use_threads = console.input("[bold green]Ingin menggunakan threads? (y/n): [/bold green]").strip().lower()
        
        list_ip = baca_list(file_path)

        if use_threads == 'y':
            num_threads = int(console.input("[bold green]Berapa jumlah thread? (contoh: 3): [/bold green]").strip())
            cek_domain_threaded(list_ip, result_file, num_threads)
        else:
            for ip in list_ip:
                process_ip(ip, requests.Session(), result_file)

    else:
        console.print("[bold red]Pilihan tidak valid. Program dihentikan.[/bold red]")

if __name__ == "__main__":
    main()
