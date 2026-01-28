import requests
import json
import os
import random
import time
from eth_account import Account
from mnemonic import Mnemonic
from datetime import datetime, timezone
from colorama import init, Fore, Style
from eth_account.messages import encode_defunct

# Initialize colorama
init()

# Enable HD wallet features
Account.enable_unaudited_hdwallet_features()

# ======================= CONFIGURATION =======================
BASE_URL = 'https://settlr.finance'
WALLET_FILE = './wallet.json'
PROXY_FILE = './proxy.txt'

# Registration settings
DELAY_MIN_SECONDS = 3
DELAY_MAX_SECONDS = 7
MAX_RETRIES = 3

# ======================= FINGERPRINT GENERATOR =======================
def generate_fingerprint():
    chrome_versions = ['120', '121', '122', '123', '124', '125', '126', '127', '128', '129', '130', '131', '132', '133', '134', '135', '136', '137', '138', '139', '140', '141', '142', '143', '144']
    platforms = ['Windows', 'Linux', 'macOS']
    languages = ['en-US', 'en-GB', 'en-CA', 'en-AU']

    chrome_version = random.choice(chrome_versions)
    platform = random.choice(platforms)
    language = random.choice(languages)

    if platform == 'Windows':
        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"
    elif platform == 'Linux':
        user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"
    else:
        user_agent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"

    sec_ch_ua = f'"Not(A:Brand";v="8", "Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}"'

    return {
        'userAgent': user_agent,
        'secChUa': sec_ch_ua,
        'secChUaPlatform': f'"{platform}"',
        'acceptLanguage': f'{language},en;q=0.9',
        'chromeVersion': chrome_version,
        'platform': platform
    }

# ======================= PROXY FUNCTIONS =======================
def load_proxies():
    try:
        if not os.path.exists(PROXY_FILE):
            return []
        with open(PROXY_FILE, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return proxies
    except:
        return []

def get_proxy_dict(proxy_line):
    if not proxy_line:
        return None
    if proxy_line.startswith("http://") or proxy_line.startswith("https://"):
        proxy_url = proxy_line
    else:
        proxy_url = f"http://{proxy_line}"
    return {
        "http": proxy_url,
        "https": proxy_url
    }

def get_proxy_display(proxy_line):
    if not proxy_line:
        return ''
    try:
        if '@' in proxy_line:
            host_port = proxy_line.split('@')[-1]
            return f":{host_port.split(':')[-1]}"
        return ''
    except:
        return ''

# ======================= WALLET FUNCTIONS =======================
def load_wallets():
    try:
        if not os.path.exists(WALLET_FILE):
            return []
        with open(WALLET_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_wallets(wallets):
    with open(WALLET_FILE, 'w', encoding='utf-8') as f:
        json.dump(wallets, f, indent=2)

def short_addr(addr):
    return f"{addr[:8]}...{addr[-6:]}"

# ======================= API FUNCTIONS =======================
def get_headers(fingerprint, csrf_token=None, referrer=None):
    headers = {
        "accept": "*/*",
        "accept-language": fingerprint['acceptLanguage'],
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua": fingerprint['secChUa'],
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": fingerprint['secChUaPlatform'],
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": fingerprint['userAgent']
    }
    
    if csrf_token:
        headers["x-csrf-token"] = csrf_token
    if referrer:
        headers["referer"] = referrer
    
    return headers

def get_csrf_token(session, fingerprint, proxies=None):
    try:
        headers = get_headers(fingerprint)
        response = session.get(
            f"{BASE_URL}/api/csrf-token",
            headers=headers,
            proxies=proxies,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("csrfToken")
        else:
            print(f"{Fore.RED}  ✗ CSRF Error: {response.status_code} - {response.text[:200]}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}  ✗ CSRF Exception: {str(e)}{Style.RESET_ALL}")
        return None

def get_challenge_nonce(session, fingerprint, csrf_token, wallet_address, proxies=None):
    try:
        headers = get_headers(fingerprint, csrf_token, f"{BASE_URL}/?ref=")
        headers["content-type"] = "application/json"
        
        payload = {"walletAddress": wallet_address.lower()}
        
        response = session.post(
            f"{BASE_URL}/api/auth/challenge",
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("nonce")
        else:
            print(f"{Fore.RED}  ✗ Nonce Error: {response.status_code} - {response.text[:200]}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}  ✗ Nonce Exception: {str(e)}{Style.RESET_ALL}")
        return None

def sign_message(message, private_key):
    account = Account.from_key(private_key)
    message_hash = encode_defunct(text=message)
    signed_message = account.sign_message(message_hash)
    # Add 0x prefix to signature
    signature = "0x" + signed_message.signature.hex()
    return signature, account.address

def connect_wallet(session, fingerprint, csrf_token, wallet_address, nonce, signature, referral_code, proxies=None):
    try:
        headers = get_headers(fingerprint, csrf_token, f"{BASE_URL}/?ref={referral_code}")
        headers["content-type"] = "application/json"
        
        message = "Sign in to Settlr\n\nThis request will not trigger a blockchain transaction or cost any gas fees.\n\nNonce: " + nonce
        
        payload = {
            "walletAddress": wallet_address.lower(),
            "message": message,
            "signature": signature,
            "nonce": nonce,
            "referralCode": referral_code
        }
        
        response = session.post(
            f"{BASE_URL}/api/wallet/connect",
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{Fore.RED}  ✗ Connect Error: {response.status_code} - {response.text[:300]}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}  ✗ Connect Exception: {str(e)}{Style.RESET_ALL}")
        return None

def complete_social_task(session, fingerprint, csrf_token, task, proxies=None):
    try:
        headers = get_headers(fingerprint, csrf_token, f"{BASE_URL}/earn")
        headers["content-type"] = "application/json"
        
        payload = {"task": task}
        
        response = session.post(
            f"{BASE_URL}/api/earn/social",
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("pointsAwarded", 0)
            else:
                print(f"{Fore.YELLOW}  ⚠ {task.capitalize()}: {data.get('message', 'Unknown response')}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}  ✗ {task.capitalize()} Error: {response.status_code} - {response.text[:200]}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}  ✗ {task.capitalize()} Exception: {str(e)}{Style.RESET_ALL}")
        return None

def execute_trade(session, fingerprint, csrf_token, market_id, side, size, leverage, proxies=None):
    try:
        headers = get_headers(fingerprint, csrf_token, f"{BASE_URL}/market/{market_id}")
        headers["content-type"] = "application/json"
        
        payload = {
            "marketId": market_id,
            "side": side,
            "size": size,
            "leverage": leverage
        }
        
        response = session.post(
            f"{BASE_URL}/api/positions",
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=30
        )
        
        # Accept both 200 and 201 (Created) as success
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"{Fore.RED}  ✗ Trade Error: {response.status_code} - {response.text[:200]}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}  ✗ Trade Exception: {str(e)}{Style.RESET_ALL}")
        return None

# ======================= DISPLAY FUNCTIONS =======================
def display_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print()
    print(f"{Fore.YELLOW}  _____   ___ ______  ______  _      ____  {Style.RESET_ALL}")
    print(f"{Fore.YELLOW} / ___/  /  _]      ||      || |    |    \\ {Style.RESET_ALL}")
    print(f"{Fore.YELLOW}(   \\_  /  [_|      ||      || |    |  D  ){Style.RESET_ALL}")
    print(f"{Fore.YELLOW} \\__  ||    _]_|  |_||_|  |_|| |___ |    / {Style.RESET_ALL}")
    print(f"{Fore.YELLOW} /  \\ ||   [_  |  |    |  |  |     ||    \\ {Style.RESET_ALL}")
    print(f"{Fore.YELLOW} \\    ||     | |  |    |  |  |     ||  .  \\{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  \\___||_____| |__|    |__|  |_____||__|\\_|{Style.RESET_ALL}")
    print()
    print(f"{Fore.GREEN}          https://t.me/MDFKOfficial         {Style.RESET_ALL}")
    print()

def display_menu():
    wallets = load_wallets()
    proxies = load_proxies()
    registered = len([w for w in wallets if w.get('registered')])
    
    print(f"{Fore.WHITE}📁 Wallets: {len(wallets)} | ✓ Registered: {registered} | 🌐 Proxies: {len(proxies)}{Style.RESET_ALL}")
    print()
    print(f"{Fore.WHITE} [1] Generate Wallets{Style.RESET_ALL}")
    print(f"{Fore.WHITE} [2] Auto Register{Style.RESET_ALL}")
    print(f"{Fore.WHITE} [3] Auto Complete Missions{Style.RESET_ALL}")
    print(f"{Fore.RED} [0] Exit{Style.RESET_ALL}")
    print()

def log(log_type, msg):
    icons = {'ok': '✓', 'err': '✗', 'warn': '⚠', 'info': '→'}
    colors = {'ok': Fore.GREEN, 'err': Fore.RED, 'warn': Fore.YELLOW, 'info': Fore.WHITE}
    print(f"{colors[log_type]}  {icons[log_type]} {msg}{Style.RESET_ALL}")

# ======================= FEATURE 1: GENERATE WALLETS =======================
def handle_generate_wallets():
    print(f"\n{Fore.YELLOW}📦 GENERATE WALLETS{Style.RESET_ALL}\n")
    
    try:
        count = int(input(f"{Fore.WHITE}How many wallets? {Style.RESET_ALL}"))
        if count <= 0:
            log('err', 'Invalid number')
            return
    except ValueError:
        log('err', 'Invalid number')
        return
    
    wallets = load_wallets()
    proxies = load_proxies()
    
    print()
    mnemo = Mnemonic("english")
    for i in range(count):
        mnemonic = mnemo.generate(strength=128)
        account = Account.from_mnemonic(mnemonic)
        fingerprint = generate_fingerprint()
        
        wallet_data = {
            'id': len(wallets) + 1,
            'address': account.address,
            'privateKey': account._private_key.hex(),
            'mnemonic': mnemonic,
            'fingerprint': fingerprint,
            'registered': False,
            'referralCode': '',
            'missionsCompleted': False,
            'traded': False,
            'stlrPoints': 0,
            'createdAt': datetime.now(timezone.utc).isoformat()
        }
        wallets.append(wallet_data)
        
        proxy_index = (len(wallets) - 1) % (len(proxies) if proxies else 1)
        proxy = proxies[proxy_index] if proxies else None
        proxy_info = f"{Fore.WHITE} [proxy{get_proxy_display(proxy)}]{Style.RESET_ALL}" if proxy else f"{Fore.WHITE} [local]{Style.RESET_ALL}"
        print(f"{Fore.GREEN}  [{i + 1}/{count}] {short_addr(account.address)}{proxy_info}{Style.RESET_ALL}")
    
    save_wallets(wallets)
    print(f"\n{Fore.CYAN}✓ Generated {count} wallets | Total: {len(wallets)}{Style.RESET_ALL}\n")

# ======================= FEATURE 2: AUTO REGISTER =======================
def handle_auto_register():
    print(f"\n{Fore.YELLOW}📝 AUTO REGISTER{Style.RESET_ALL}\n")
    
    wallets = load_wallets()
    unregistered = [w for w in wallets if not w.get('registered')]
    
    if not wallets:
        log('err', 'No wallets found. Generate wallets first.')
        return
    
    print(f"{Fore.WHITE}Total: {len(wallets)} | Unregistered: {len(unregistered)}{Style.RESET_ALL}\n")
    
    if not unregistered:
        log('warn', 'All wallets already registered')
        return
    
    referral_code = input(f"{Fore.WHITE}Referral code: {Style.RESET_ALL}").strip()
    if not referral_code:
        log('err', 'Referral code is required!')
        return
    
    print()
    success = 0
    failed = 0
    
    proxies = load_proxies()
    print(f"{Fore.WHITE}Loaded {len(proxies)} proxies | Delay: {DELAY_MIN_SECONDS}-{DELAY_MAX_SECONDS}s | Max retries: {MAX_RETRIES}{Style.RESET_ALL}\n")
    
    for i, wallet in enumerate(wallets):
        if wallet.get('registered'):
            continue
        
        registered = False
        used_proxy_indices = []
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            # Get proxy
            if proxies:
                if attempt == 0:
                    proxy_index = i % len(proxies)
                else:
                    for idx in range(len(proxies)):
                        if idx not in used_proxy_indices:
                            proxy_index = idx
                            break
                    else:
                        proxy_index = random.randint(0, len(proxies) - 1)
                used_proxy_indices.append(proxy_index)
                proxy = proxies[proxy_index]
            else:
                proxy = None
            
            proxy_dict = get_proxy_dict(proxy)
            fingerprint = wallet.get('fingerprint') or generate_fingerprint()
            proxy_info = f"{Fore.WHITE} [proxy{get_proxy_display(proxy)}]{Style.RESET_ALL}" if proxy else f"{Fore.WHITE} [local]{Style.RESET_ALL}"
            attempt_info = f"{Fore.YELLOW} [retry {attempt}/{MAX_RETRIES - 1}]{Style.RESET_ALL}" if attempt > 0 else ''
            
            print(f"{Fore.CYAN}[{i + 1}/{len(wallets)}] {short_addr(wallet['address'])}{proxy_info}{attempt_info}{Style.RESET_ALL}")
            
            # Create session
            session = requests.Session()
            
            # Step 1: Get CSRF token
            csrf_token = get_csrf_token(session, fingerprint, proxy_dict)
            if not csrf_token:
                last_error = 'Failed to get CSRF token'
                if attempt >= MAX_RETRIES - 1:
                    log('err', last_error)
                    failed += 1
                continue
            
            # Step 2: Get challenge nonce
            nonce = get_challenge_nonce(session, fingerprint, csrf_token, wallet['address'], proxy_dict)
            if not nonce:
                last_error = 'Failed to get nonce'
                if attempt >= MAX_RETRIES - 1:
                    log('err', last_error)
                    failed += 1
                continue
            
            # Step 3: Sign message
            message = "Sign in to Settlr\n\nThis request will not trigger a blockchain transaction or cost any gas fees.\n\nNonce: " + nonce
            signature, signer_address = sign_message(message, wallet['privateKey'])
            
            # Debug output
            if attempt == 0:  # Only show on first attempt
                print(f"{Fore.CYAN}  → Debug: Message length: {len(message)}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}  → Debug: Signature: {signature[:20]}...{Style.RESET_ALL}")
                print(f"{Fore.CYAN}  → Debug: Signer: {signer_address}{Style.RESET_ALL}")
            
            # Verify address
            if signer_address.lower() != wallet['address'].lower():
                last_error = f"Address mismatch! Expected {wallet['address']}, got {signer_address}"
                if attempt >= MAX_RETRIES - 1:
                    log('err', last_error)
                    failed += 1
                continue
            
            # Step 4: Connect wallet
            result = connect_wallet(session, fingerprint, csrf_token, wallet['address'], nonce, signature, referral_code, proxy_dict)
            
            if result:
                wallet['registered'] = True
                wallet['referralCode'] = referral_code
                log('ok', f"Registered | Balance: {result.get('balance', 0)} STLR")
                success += 1
                registered = True
                break
            else:
                last_error = 'Registration failed'
                if attempt >= MAX_RETRIES - 1:
                    log('err', last_error)
                    failed += 1
        
        # Save progress
        save_wallets(wallets)
        
        # Add delay between registrations
        remaining = len([w for idx, w in enumerate(wallets) if idx > i and not w.get('registered')])
        if remaining > 0:
            delay = random.randint(DELAY_MIN_SECONDS, DELAY_MAX_SECONDS)
            print(f"{Fore.WHITE}⏳ Waiting {delay}s before next registration...{Style.RESET_ALL}\n")
            time.sleep(delay)
    
    save_wallets(wallets)
    print(f"\n{Fore.CYAN}✓ Done | Success: {success} | Failed: {failed}{Style.RESET_ALL}\n")

# ======================= FEATURE 3: AUTO COMPLETE MISSIONS =======================
def handle_auto_complete_missions():
    print(f"\n{Fore.YELLOW}🎯 AUTO COMPLETE MISSIONS{Style.RESET_ALL}\n")
    
    wallets = load_wallets()
    registered = [w for w in wallets if w.get('registered')]
    
    if not registered:
        log('err', 'No registered wallets found')
        return
    
    print(f"{Fore.WHITE}Registered accounts: {len(registered)}{Style.RESET_ALL}\n")
    
    missions_done = 0
    trades_done = 0
    failed = 0
    total_points = 0
    
    proxies = load_proxies()
    
    for i, wallet in enumerate(wallets):
        if not wallet.get('registered'):
            continue
        
        proxy_index = i % (len(proxies) if proxies else 1)
        proxy = proxies[proxy_index] if proxies else None
        proxy_dict = get_proxy_dict(proxy)
        fingerprint = wallet.get('fingerprint') or generate_fingerprint()
        proxy_info = f"{Fore.WHITE} [proxy{get_proxy_display(proxy)}]{Style.RESET_ALL}" if proxy else f"{Fore.WHITE} [local]{Style.RESET_ALL}"
        
        print(f"{Fore.CYAN}[{i + 1}/{len(wallets)}] {short_addr(wallet['address'])}{proxy_info}{Style.RESET_ALL}")
        
        # Create session and login
        session = requests.Session()
        
        # Get CSRF token
        csrf_token = get_csrf_token(session, fingerprint, proxy_dict)
        if not csrf_token:
            log('err', 'Failed to get CSRF token')
            failed += 1
            time.sleep(3)
            continue
        
        # Get nonce
        nonce = get_challenge_nonce(session, fingerprint, csrf_token, wallet['address'], proxy_dict)
        if not nonce:
            log('err', 'Failed to get nonce')
            failed += 1
            time.sleep(3)
            continue
        
        # Sign and login
        message = "Sign in to Settlr\n\nThis request will not trigger a blockchain transaction or cost any gas fees.\n\nNonce: " + nonce
        signature, _ = sign_message(message, wallet['privateKey'])
        
        login_result = connect_wallet(session, fingerprint, csrf_token, wallet['address'], nonce, signature, wallet.get('referralCode', ''), proxy_dict)
        
        if not login_result:
            log('err', 'Login failed')
            failed += 1
            time.sleep(3)
            continue
        
        log('ok', 'Login successful')
        
        # Complete missions if not done
        if not wallet.get('missionsCompleted'):
            # Get new CSRF token for missions
            csrf_token = get_csrf_token(session, fingerprint, proxy_dict)
            if not csrf_token:
                log('warn', 'Failed to get CSRF for missions')
            else:
                points_earned = 0
                
                # Twitter mission
                twitter_points = complete_social_task(session, fingerprint, csrf_token, "twitter", proxy_dict)
                if twitter_points:
                    log('ok', f"Twitter → +{twitter_points} STLR")
                    points_earned += twitter_points
                
                time.sleep(random.randint(2, 4))
                
                # Telegram mission
                telegram_points = complete_social_task(session, fingerprint, csrf_token, "telegram", proxy_dict)
                if telegram_points:
                    log('ok', f"Telegram → +{telegram_points} STLR")
                    points_earned += telegram_points
                
                if points_earned > 0:
                    wallet['missionsCompleted'] = True
                    wallet['stlrPoints'] += points_earned
                    total_points += points_earned
                    missions_done += 1
                    log('ok', f"Missions completed → Total: {points_earned} STLR")
        
        # Execute trade if not done
        if not wallet.get('traded'):
            # Get new CSRF token for trade
            csrf_token = get_csrf_token(session, fingerprint, proxy_dict)
            if not csrf_token:
                log('warn', 'Failed to get CSRF for trade')
            else:
                # Random trade parameters
                side = random.choice(["YES", "NO"])
                size = random.randint(100, 1000)
                leverage = 10
                market_id = 2
                
                trade_result = execute_trade(session, fingerprint, csrf_token, market_id, side, size, leverage, proxy_dict)
                
                if trade_result:
                    wallet['traded'] = True
                    entry = trade_result.get('entryProbability')
                    liq = trade_result.get('liquidationProbability')
                    log('ok', f"Trade: {side} | Size: {size} | {leverage}x | Entry: {entry}% | Liq: {liq}%")
                    trades_done += 1
                else:
                    log('warn', 'Trade failed')
        
        # Save progress
        save_wallets(wallets)
        
        # Wait before next account
        time.sleep(3)
    
    save_wallets(wallets)
    print(f"\n{Fore.CYAN}✓ Done | Missions: {missions_done} | Trades: {trades_done} | Failed: {failed} | +{total_points} pts{Style.RESET_ALL}\n")

# ======================= MAIN FUNCTION =======================
def main():
    display_banner()
    
    while True:
        display_menu()
        choice = input(f"{Fore.WHITE}Select: {Style.RESET_ALL}").strip()
        
        if choice == '1':
            handle_generate_wallets()
        elif choice == '2':
            handle_auto_register()
        elif choice == '3':
            handle_auto_complete_missions()
        elif choice == '0':
            print(f"\n{Fore.CYAN}Goodbye! 👋{Style.RESET_ALL}\n")
            break
        else:
            print(f"\n{Fore.RED}Invalid option{Style.RESET_ALL}\n")
        
        input(f"{Fore.WHITE}Press Enter...{Style.RESET_ALL}")
        display_banner()

if __name__ == "__main__":
    main()
