import discord
import asyncio
import aiohttp
import json
import os
from datetime import datetime
from colorama import Fore, init, Style, Back
from pyfiglet import Figlet
import random
import time

init(autoreset=True)

# ===== CONFIGURATION =====
CONFIG = {
    'input_file': 'tokens.txt',
    'output_dir': 'results',
    'timeout': 10,
    'max_concurrent': 200,
    'show_animation': True
}

# ===== UI DESIGN =====
class ConsoleUI:
    COLORS = {
        'primary': '\033[38;5;213m',
        'secondary': '\033[38;5;183m',
        'success': '\033[38;5;48m',
        'error': '\033[38;5;196m',
        'warning': '\033[38;5;214m',
        'info': '\033[38;5;39m'
    }
    
    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def print_banner():
        ConsoleUI.clear()
        f = Figlet(font='doom')
        banner = f.renderText('Token Checker')
        print(f"{ConsoleUI.COLORS['primary']}{banner}")
        print(f"{' '*18}{ConsoleUI.COLORS['secondary']}v5.0 PRO EDITION")
        print(f"\n{ConsoleUI.COLORS['info']}{'═'*60}")
        print(f"{' '*15}Lunar Development • discord.gg/lunardevs")
        print(f"{ConsoleUI.COLORS['info']}{'═'*60}\n")
    
    @staticmethod
    def print_status(current, total, working, dead):
        progress = current/total
        bar_length = 40
        filled = int(bar_length * progress)
        bar = f"{ConsoleUI.COLORS['success']}{'█'*filled}" + \
              f"{ConsoleUI.COLORS['secondary']}{'░'*(bar_length-filled)}"
        
        print(f"\n{ConsoleUI.COLORS['primary']}┌{'─'*58}┐")
        print(f"│ {bar} {progress:.1%} │")
        print(f"├{'─'*58}┤")
        print(f"│ {ConsoleUI.COLORS['success']}✓ LIVE: {working} " + 
              f"{ConsoleUI.COLORS['error']}✗ DEAD: {dead} " +
              f"{ConsoleUI.COLORS['info']}⚡ REMAINING: {total-current} │")
        print(f"└{'─'*58}┘\n")
    
    @staticmethod
    def print_account(account):
        nitro = ""
        if account['premium'] > 0:
            nitro = f"{ConsoleUI.COLORS['warning']}NITRO✨ "
        
        print(f"{ConsoleUI.COLORS['success']}✔ {nitro}" +
              f"{ConsoleUI.COLORS['primary']}{account['username']:<25} " +
              f"{ConsoleUI.COLORS['secondary']}{account['email']:<30} " +
              f"{ConsoleUI.COLORS['info']}{account['phone']}")

# ===== CORE LOGIC =====
async def check_token(session, token, semaphore):
    headers = {'Authorization': token}
    url = 'https://discord.com/api/v9/users/@me'
    
    async with semaphore:
        try:
            async with session.get(url, headers=headers, timeout=CONFIG['timeout']) as r:
                if r.status == 200:
                    data = await r.json()
                    return {
                        'token': token,
                        'username': f"{data['username']}#{data['discriminator']}",
                        'id': data['id'],
                        'email': data.get('email', 'None'),
                        'phone': data.get('phone', 'None'),
                        'verified': data.get('verified', False),
                        'premium': data.get('premium_type', 0),
                        'locale': data.get('locale', 'en-US'),
                        'mfa': data.get('mfa_enabled', False)
                    }
                return {'token': token, 'status': 'dead'}
        except Exception as e:
            return {'token': token, 'status': 'dead', 'error': str(e)}

async def main():
    ConsoleUI.print_banner()
    
    # Initialize
    if not os.path.exists(CONFIG['output_dir']):
        os.makedirs(CONFIG['output_dir'])
    
    # Load tokens
    try:
        with open(CONFIG['input_file'], 'r') as f:
            tokens = [line.strip() for line in f if line.strip()]
    except:
        print(f"{ConsoleUI.COLORS['error']}ERROR: tokens.txt not found!")
        return

    if not tokens:
        print(f"{ConsoleUI.COLORS['error']}ERROR: No tokens found!")
        return

    # Process tokens
    working = []
    dead = []
    current = 0
    
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(CONFIG['max_concurrent'])
        tasks = [check_token(session, token, semaphore) for token in tokens]
        
        for future in asyncio.as_completed(tasks):
            result = await future
            current += 1
            
            if 'status' not in result:  # Working account
                working.append(result)
                ConsoleUI.print_account(result)
            else:
                dead.append(result['token'])
            
            if current % 5 == 0 or current == len(tokens):
                ConsoleUI.print_status(current, len(tokens), len(working), len(dead))
            
            if CONFIG['show_animation'] and random.random() < 0.1:
                time.sleep(0.05)  # Smooth animation effect

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Working tokens
    with open(f"{CONFIG['output_dir']}/working_{timestamp}.txt", 'w') as f:
        f.write('\n'.join([acc['token'] for acc in working]))
    
    # 2. Full data (JSON)
    with open(f"{CONFIG['output_dir']}/accounts_{timestamp}.json", 'w') as f:
        json.dump(working, f, indent=4)
    
    # 3. Email:Phone data
    with open(f"{CONFIG['output_dir']}/credentials_{timestamp}.txt", 'w') as f:
        f.write('\n'.join([f"{acc['email']}:{acc['phone']}" for acc in working]))
    
    # 4. Dead tokens
    with open(f"{CONFIG['output_dir']}/dead_{timestamp}.txt", 'w') as f:
        f.write('\n'.join(dead))

    # Final report
    ConsoleUI.print_banner()
    print(f"{ConsoleUI.COLORS['primary']}┌{'─'*58}┐")
    print(f"│ {ConsoleUI.COLORS['info']}🚀 VALIDATION COMPLETE {' '*34}│")
    print(f"├{'─'*58}┤")
    print(f"│ {ConsoleUI.COLORS['success']}✓ LIVE ACCOUNTS: {len(working):<42}│")
    print(f"│ {ConsoleUI.COLORS['error']}✗ DEAD TOKENS: {len(dead):<43}│")
    print(f"│ {ConsoleUI.COLORS['warning']}⚡ SUCCESS RATE: {len(working)/len(tokens):.2%}{' '*36}│")
    if working:
        nitro_count = sum(1 for acc in working if acc['premium'] > 0)
        print(f"│ {ConsoleUI.COLORS['warning']}💎 NITRO ACCOUNTS: {nitro_count}{' '*38}│")
    print(f"└{'─'*58}┘")
    print(f"\n{ConsoleUI.COLORS['secondary']}📁 Results saved to /{CONFIG['output_dir']} with timestamp: {timestamp}")
    print(f"{ConsoleUI.COLORS['primary']}🔗 discord.gg/lunardevs\n")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{ConsoleUI.COLORS['error']}🚫 Operation cancelled by user")
