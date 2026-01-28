# SETTLR Automation Bot (Python)

Automation bot for [Settlr Finance](https://settlr.finance) platform that supports auto registration, mission completion, and trade execution.

## 📋 Features

- **Generate Wallets** - Create Ethereum wallets with mnemonic and private key
- **Auto Register** - Automatically register wallets to Settlr platform with referral code
- **Auto Complete Missions** - Complete social media missions (Twitter, Telegram) and execute trades automatically

## 🛠️ Requirements

### Python Package Dependencies

```bash
pip install requests eth-account mnemonic colorama
```

**Dependency List:**
- `requests` - HTTP requests
- `eth-account` - Ethereum account management
- `mnemonic` - BIP39 mnemonic phrase generation
- `colorama` - Terminal color output

### File Requirements

1. **proxy.txt** (Optional) - Proxy list for IP rotation
   ```
   username:password@host:port
   host:port:username:password
   http://username:password@host:port
   ```

2. **wallet.json** (Auto-generated) - Stores created wallet data

## 🚀 Usage Guide

### 1. Install Dependencies

```bash
pip install requests eth-account mnemonic colorama
```

### 2. Run the Bot

```bash
python main.py
```

### 3. Main Menu

```
📁 Wallets: 0 | ✓ Registered: 0 | 🌐 Proxies: 0

 [1] Generate Wallets
 [2] Auto Register
 [3] Auto Complete Missions
 [0] Exit
```

## 📖 Feature Guide

### Generate Wallets (Menu 1)

Create new Ethereum wallets with:
- Mnemonic phrase (12 words)
- Private key
- Public address
- Random browser fingerprint
- Auto-assign proxy (if available)

**Example:**
```
How many wallets? 5
```

### Auto Register (Menu 2)

Register wallets to Settlr platform:
- Input referral code (required)
- Auto login with wallet signature
- Retry mechanism with max 3 attempts
- Random delay 3-7 seconds between registrations

**Example:**
```
Referral code: YOUR_REF_CODE
```

### Auto Complete Missions (Menu 3)

Complete missions and trading:

**Social Missions:**
- Twitter Follow/Like
- Telegram Join

**Trading:**
- Side: YES/NO (random)
- Size: 100-1000 (random)
- Leverage: 10x
- Market ID: 2

## ⚙️ Configuration

Edit the `CONFIGURATION` section in [`main.py`](file:///c:/Users/NHQNA/Downloads/2025%20BOT%20NEW/BOT/SETTLR/main.py#L18-L26):

```python
BASE_URL = 'https://settlr.finance'
WALLET_FILE = './wallet.json'
PROXY_FILE = './proxy.txt'

# Registration settings
DELAY_MIN_SECONDS = 3
DELAY_MAX_SECONDS = 7
MAX_RETRIES = 3
```

## 📁 File Structure

```
SETTLR/
├── main.py           # Main script
├── README.md         # Documentation (this file)
├── proxy.txt         # Proxy list (optional)
└── wallet.json       # Wallet data (auto-generated)
```

## 🔐 wallet.json Format

```json
[
  {
    "id": 1,
    "address": "0x...",
    "privateKey": "...",
    "mnemonic": "word1 word2 ... word12",
    "fingerprint": {
      "userAgent": "...",
      "secChUa": "...",
      "secChUaPlatform": "...",
      "acceptLanguage": "...",
      "chromeVersion": "...",
      "platform": "..."
    },
    "registered": false,
    "referralCode": "",
    "missionsCompleted": false,
    "traded": false,
    "stlrPoints": 0,
    "createdAt": "2026-01-28T00:00:00+00:00"
  }
]
```

## 🎯 Bot Workflow

### Registration Flow:
1. Generate unique fingerprint
2. Get CSRF token
3. Get challenge nonce
4. Sign message with private key
5. Submit wallet connect with signature
6. Save status to `wallet.json`

### Mission Flow:
1. Login with signature
2. Complete Twitter mission
3. Complete Telegram mission
4. Execute random trade (YES/NO)
5. Update points and status

## ⚠️ Important Notes

> [!WARNING]
> **SECURITY**
> - Never share `wallet.json` or any file containing private keys
> - Use proxies to avoid rate limiting
> - Keep backup of mnemonic phrases in a secure location

> [!IMPORTANT]
> **REQUIREMENTS**
> - Referral code is mandatory for registration
> - Wallet must be registered before completing missions
> - Each wallet uses a unique fingerprint

> [!TIP]
> **OPTIMIZATION**
> - Use different proxies for each wallet
> - Set adequate delays to avoid rate limiting
> - Monitor logs for troubleshooting

## 🐛 Troubleshooting

### Error: "Failed to get CSRF token"
- Check internet connection
- Try changing proxy
- Ensure BASE_URL is correct

### Error: "Address mismatch"
- Private key doesn't match the address
- Regenerate wallet

### Error: "Registration failed"
- Invalid referral code
- Rate limiting (wait a few minutes)
- Proxy issues

## 📞 Support

- Telegram: [@MDFKOfficial](https://t.me/MDFKOfficial)
- Platform: [https://settlr.finance](https://settlr.finance)

## 📄 License

This script is for educational purposes only. Use at your own risk.

---

**Created:** 2026-01-28  
**Version:** 1.0.0  
**Author:** MDFK Official
