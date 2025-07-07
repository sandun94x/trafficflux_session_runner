import asyncio
import random
import json
import requests
import platform
from fake_useragent import UserAgent
from playwright.async_api import async_playwright
import time

# Fix for Windows subprocess issues with asyncio
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Initialize user agent generator
ua_generator = UserAgent()

# Webshare proxy configuration
WEBSHARE_PROXY_CONFIG = {
    "username": "hvxjsarm-rotate",
    "password": "dku232fuxt1s",
    "session_id": "mysession1",  
    "server": "p.webshare.io",
    "hostname": "p.webshare.io",
    "port": 80
}

def get_proxy_location_via_webshare():
    """Get proxy location information via Webshare proxy"""
    try:
        print("Detecting proxy location via Webshare...")
        response = requests.get(
            "http://ip-api.com/json",
            proxies={
                "http": f"http://{WEBSHARE_PROXY_CONFIG['username']}:{WEBSHARE_PROXY_CONFIG['password']}@p.webshare.io:80/",
                "https": f"http://{WEBSHARE_PROXY_CONFIG['username']}:{WEBSHARE_PROXY_CONFIG['password']}@p.webshare.io:80/"
            },
            timeout=10
        )
        data = response.json()
        
        proxy_info = {
            "ip": data.get("query", "Unknown"),
            "latitude": data.get("lat", 40.7128),
            "longitude": data.get("lon", -74.006),
            "timezone": data.get("timezone", "America/New_York"),
            "country": data.get("country", "Unknown"),
            "city": data.get("city", "Unknown")
        }
        
        print(f"Proxy Location: {proxy_info['city']}, {proxy_info['country']} (IP: {proxy_info['ip']})")
        return proxy_info
        
    except Exception as e:
        print(f"Failed to get proxy location: {e}")
        return {
            "ip": "Unknown",
            "latitude": 40.7128,
            "longitude": -74.006,
            "timezone": "America/New_York",
            "country": "US",
            "city": "New York"
        }
# ...existing code...

# Desktop Chrome-only user agents - Updated to match Playwright Chromium
CHROMIUM_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
]

def get_random_user_agent():
    """Get a random Chrome/Chromium user agent that matches Playwright's Chromium version"""
    # Use Playwright's actual Chromium version (130.x)
    playwright_compatible_uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", 
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ]
    
    ua_static = random.choice(playwright_compatible_uas)
    print(f"[INFO] Using Playwright-compatible UA: {ua_static}")
    return ua_static

def random_user_agent_data():
    """Generate Chrome-specific user agent data that matches Playwright's actual browser version"""
    # Match Playwright's actual Chromium version (130.x)
    chrome_version = 130
    brands = [
        {"brand": "Chromium", "version": "130"},
        {"brand": "Not?A_Brand", "version": "99"}, 
        {"brand": "Google Chrome", "version": "130"}
    ]
    
    platform = random.choice(["Windows", "macOS", "Linux"])
    platform_version = random.choice(["10.0", "11.0", "14.0"])
    ua_full_version = f"130.0.{random.randint(6000,7000)}.{random.randint(100,999)}"
    
    return {
        "brands": brands,
        "mobile": False,
        "getHighEntropyValues": {
            "architecture": "x86",
            "model": "",
            "platform": platform,
            "platformVersion": platform_version,
            "uaFullVersion": ua_full_version,
            "bitness": "64",
            "fullVersionList": [
                {"brand": "Chromium", "version": ua_full_version},
                {"brand": "Google Chrome", "version": ua_full_version}
            ]
        }
    }

def random_languages():
    return random.choice([['en-US', 'en'], ['fr-FR', 'fr'], ['es-ES', 'es']])

def random_platform():
    return random.choice(['Win32', 'MacIntel', 'Linux x86_64'])

def random_hardware_concurrency():
    return random.choice([2, 4, 8, 16])

def random_device_memory():
    return random.choice([4, 8, 16])

def random_plugins():
    return random.sample(range(1, 10), random.randint(3, 7))

def random_webgl_vendor():
    return random.choice(['Intel Inc.', 'NVIDIA Corporation', 'AMD'])

def random_webgl_renderer():
    return random.choice(['Intel Iris OpenGL Engine', 'NVIDIA GeForce GTX', 'AMD Radeon Pro'])

def random_screen_size():
    width = random.choice([1366, 1440, 1536, 1920, 2560])
    height = random.choice([768, 900, 1080, 1440])
    return width, height

def random_audio_context_hash():
    import hashlib
    random_data = f"{random.random()}{random.randint(1000, 9999)}{time.time()}"
    return hashlib.md5(random_data.encode()).hexdigest()[:16]

def random_canvas_hash():
    import hashlib
    canvas_data = f"canvas_{random.uniform(0.1, 0.9)}_{random.randint(100, 999)}"
    return hashlib.md5(canvas_data.encode()).hexdigest()[:16]

def random_webgl_hash():
    import hashlib
    webgl_data = f"webgl_{random.choice(['NVIDIA', 'AMD', 'Intel'])}_{random.randint(1000, 9999)}"
    return hashlib.md5(webgl_data.encode()).hexdigest()[:16]


async def apply_fingerprint_spoofing(page, user_agent, proxy_info):
    """Apply comprehensive browser fingerprinting countermeasures"""
    languages = random_languages()
    platform = random_platform()
    hardware_concurrency = random_hardware_concurrency()
    device_memory = random_device_memory()
    webgl_vendor = random_webgl_vendor()
    webgl_renderer = random_webgl_renderer()
    width, height = random_screen_size()
    user_agent_data = random_user_agent_data()
    
    # Generate consistent fingerprints
    audio_hash = random_audio_context_hash()
    canvas_hash = random_canvas_hash()
    webgl_hash = random_webgl_hash()
    
    # Use proxy timezone for consistency
    proxy_timezone = proxy_info.get("timezone", "America/New_York")
    
    # Calculate timezone offset based on proxy location
    timezone_offsets = {
        "America/New_York": 300,    # EST/EDT
        "America/Los_Angeles": 480, # PST/PDT  
        "Europe/London": 0,         # GMT/BST
        "Europe/Paris": -60,        # CET/CEST
        "Asia/Tokyo": -540,         # JST
        "Australia/Sydney": -660    # AEST/AEDT
    }
    
    # Get offset for proxy timezone, default to EST if unknown
    timezone_offset = timezone_offsets.get(proxy_timezone, 300)
    
    await page.add_init_script(f"""
        // CRITICAL: Remove ALL automation traces first
        Object.defineProperty(navigator, 'webdriver', {{ 
            get: () => undefined,
            configurable: false,
            enumerable: false
        }});
        
        // Delete webdriver property completely
        delete navigator.__proto__.webdriver;
        delete navigator.webdriver;
        
        // Remove automation traces from window.chrome
        if (window.chrome && window.chrome.runtime && window.chrome.runtime.onConnect) {{
            delete window.chrome.runtime.onConnect;
        }}
        
        // Override user agent to match exactly
        Object.defineProperty(navigator, 'userAgent', {{
            get: () => '{user_agent}',
            configurable: false,
            enumerable: true
        }});
        
        // Match appVersion exactly to user agent
        Object.defineProperty(navigator, 'appVersion', {{ 
            get: () => '{user_agent}'.replace('Mozilla/', ''),
            configurable: false,
            enumerable: true
        }});
        
        // SYNCHRONIZED TIMEZONE SPOOFING - Match proxy location exactly
        const TIMEZONE_OFFSET = {timezone_offset};
        const PROXY_TIMEZONE = '{proxy_timezone}';
        
        // Override Date constructor and methods
        const OriginalDate = Date;
        Date = class extends OriginalDate {{
            constructor(...args) {{
                if (args.length === 0) {{
                    super();
                }} else {{
                    super(...args);
                }}
            }}
            
            static now() {{
                return OriginalDate.now();
            }}
            
            static UTC(...args) {{
                return OriginalDate.UTC(...args);
            }}
            
            static parse(dateString) {{
                return OriginalDate.parse(dateString);
            }}
            
            getTimezoneOffset() {{
                return TIMEZONE_OFFSET;
            }}
            
            toString() {{
                const original = super.toString();
                const sign = TIMEZONE_OFFSET <= 0 ? '+' : '-';
                const hours = String(Math.floor(Math.abs(TIMEZONE_OFFSET) / 60)).padStart(2, '0');
                const minutes = String(Math.abs(TIMEZONE_OFFSET) % 60).padStart(2, '0');
                return original.replace(/GMT[+-]\\d{{4}}/, `GMT${{sign}}${{hours}}${{minutes}}`);
            }}
            
            toTimeString() {{
                const original = super.toTimeString();
                const sign = TIMEZONE_OFFSET <= 0 ? '+' : '-';
                const hours = String(Math.floor(Math.abs(TIMEZONE_OFFSET) / 60)).padStart(2, '0');
                const minutes = String(Math.abs(TIMEZONE_OFFSET) % 60).padStart(2, '0');
                return original.replace(/GMT[+-]\\d{{4}}/, `GMT${{sign}}${{hours}}${{minutes}}`);
            }}
        }};
        
        // Copy static methods
        Object.setPrototypeOf(Date, OriginalDate);
        Object.setPrototypeOf(Date.prototype, OriginalDate.prototype);
        
        // Override Intl objects to match timezone
        const OriginalDateTimeFormat = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(...args) {{
            const options = args[1] || {{}};
            if (!options.timeZone) {{
                options.timeZone = PROXY_TIMEZONE;
                args[1] = options;
            }}
            return new OriginalDateTimeFormat(...args);
        }};
        
        // Ensure resolvedOptions returns correct timezone
        const originalResolvedOptions = OriginalDateTimeFormat.prototype.resolvedOptions;
        Intl.DateTimeFormat.prototype.resolvedOptions = function() {{
            const options = originalResolvedOptions.call(this);
            options.timeZone = PROXY_TIMEZONE;
            return options;
        }};
        
        // Language and platform consistency
        Object.defineProperty(navigator, 'languages', {{ 
            get: () => {json.dumps(languages)},
            configurable: false,
            enumerable: true
        }});
        Object.defineProperty(navigator, 'language', {{ 
            get: () => '{languages[0]}',
            configurable: false, 
            enumerable: true
        }});
        Object.defineProperty(navigator, 'platform', {{ 
            get: () => '{platform}',
            configurable: false,
            enumerable: true
        }});
        
        // Hardware properties - use realistic values
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ 
            get: () => {hardware_concurrency},
            configurable: false,
            enumerable: true
        }});
        Object.defineProperty(navigator, 'deviceMemory', {{ 
            get: () => {device_memory},
            configurable: false,
            enumerable: true
        }});
        
        // Chrome properties with consistent version 130
        window.chrome = {{
            app: {{ 
                isInstalled: false,
                InstallState: {{ DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }},
                RunningState: {{ CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }}
            }},
            webstore: {{ 
                onInstallStageChanged: {{}}, 
                onDownloadProgress: {{}}
            }},
            runtime: {{ 
                onConnect: undefined,
                onMessage: undefined,
                connect: function() {{ return undefined; }},
                sendMessage: function() {{ return undefined; }},
                getManifest: () => ({{ name: "Chromium", version: "130.0.0.0" }})
            }}
        }};
        
        // Vendor properties
        Object.defineProperty(navigator, 'vendor', {{ 
            get: () => 'Google Inc.',
            configurable: false,
            enumerable: true
        }});
        Object.defineProperty(navigator, 'vendorSub', {{ 
            get: () => '',
            configurable: false,
            enumerable: true
        }});
        Object.defineProperty(navigator, 'productSub', {{ 
            get: () => '20030107',
            configurable: false,
            enumerable: true
        }});
        
        // User Agent Data with version 130
        Object.defineProperty(navigator, 'userAgentData', {{
            get: () => ({{
                brands: {json.dumps(user_agent_data["brands"])},
                mobile: false,
                platform: '{platform}',
                getHighEntropyValues: (hints) => Promise.resolve({{
                    brands: {json.dumps(user_agent_data["brands"])},
                    mobile: false,
                    platform: '{platform}',
                    platformVersion: '{user_agent_data["getHighEntropyValues"]["platformVersion"]}',
                    architecture: '{user_agent_data["getHighEntropyValues"]["architecture"]}',
                    model: '',
                    uaFullVersion: '{user_agent_data["getHighEntropyValues"]["uaFullVersion"]}',
                    bitness: '64',
                    fullVersionList: {json.dumps(user_agent_data["getHighEntropyValues"]["fullVersionList"])}
                }})
            }}),
            configurable: false,
            enumerable: true
        }});
        
        // Realistic plugins for Chrome 130
        Object.defineProperty(navigator, 'plugins', {{
            get: () => {{
                const plugins = [];
                
                // Chrome PDF Plugin
                plugins[0] = {{
                    name: "Chrome PDF Plugin",
                    filename: "internal-pdf-viewer",
                    description: "Portable Document Format",
                    length: 1,
                    item: function(index) {{ return index === 0 ? this : null; }},
                    namedItem: function(name) {{ return name === "Chrome PDF Plugin" ? this : null; }}
                }};
                
                // Chrome PDF Viewer  
                plugins[1] = {{
                    name: "Chrome PDF Viewer",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    description: "",
                    length: 1,
                    item: function(index) {{ return index === 0 ? this : null; }},
                    namedItem: function(name) {{ return name === "Chrome PDF Viewer" ? this : null; }}
                }};
                
                plugins.length = 2;
                plugins.refresh = () => {{}};
                plugins.namedItem = (name) => {{
                    for (let i = 0; i < plugins.length; i++) {{
                        if (plugins[i].name === name) return plugins[i];
                    }}
                    return null;
                }};
                plugins.item = (index) => plugins[index] || null;
                
                return plugins;
            }},
            configurable: false,
            enumerable: true
        }});
        
        // Realistic MIME types
        Object.defineProperty(navigator, 'mimeTypes', {{
            get: () => {{
                const mimeTypes = [];
                
                mimeTypes[0] = {{
                    type: "application/pdf",
                    description: "Portable Document Format", 
                    suffixes: "pdf",
                    enabledPlugin: navigator.plugins[0]
                }};
                
                mimeTypes.length = 1;
                mimeTypes.namedItem = (name) => {{
                    for (let i = 0; i < mimeTypes.length; i++) {{
                        if (mimeTypes[i].type === name) return mimeTypes[i];
                    }}
                    return null;
                }};
                mimeTypes.item = (index) => mimeTypes[index] || null;
                
                return mimeTypes;
            }},
            configurable: false,
            enumerable: true
        }});
        
        // Minimal WebGL spoofing - be very conservative
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{webgl_vendor}';
            if (parameter === 37446) return '{webgl_renderer}';
            return getParameter.call(this, parameter);
        }};
        
        // Apply same to WebGL2
        if (window.WebGL2RenderingContext) {{
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{webgl_vendor}';
                if (parameter === 37446) return '{webgl_renderer}';
                return getParameter2.call(this, parameter);
            }};
        }}
        
        console.log('Enhanced stealth mode activated');
        console.log('Timezone:', PROXY_TIMEZONE, 'Offset:', TIMEZONE_OFFSET);
        console.log('User Agent:', navigator.userAgent);
    """)

# Update the create_new_page function to pass proxy_info
async def create_new_page(context, user_agent=None, proxy_info=None):
    """Create a new page with proper setup and proxy testing"""
    if proxy_info is None:
        proxy_info = getattr(context, '_proxy_info', {
            "ip": "127.0.0.1",
            "timezone": "America/New_York"
        })
    
    if user_agent is None:
        user_agent = get_random_user_agent()
    
    page = await context.new_page()
    
    # Set longer timeouts for proxy connections
    page.set_default_timeout(60000)
    page.set_default_navigation_timeout(60000)
    
    # Apply enhanced fingerprint spoofing
    await apply_fingerprint_spoofing(page, user_agent, proxy_info)
    
    print("[INFO] Page created and configured successfully")
    
    return page

# Update launch_stealth_browser to store full proxy_info
async def launch_stealth_browser(user_agent=None):
    """Launch a stealth browser with proxy and fingerprint protection"""
    p = await async_playwright().start()

    # Use Webshare rotating proxy for browser context - GET IP ONCE
    proxy_location = get_proxy_location_via_webshare()
    proxy_ip = proxy_location.get("ip", "127.0.0.1")

    if user_agent is None:
        user_agent = get_random_user_agent()

    print(f"[INFO] Launching browser with User Agent: {user_agent}")
    print(f"[INFO] Using Proxy IP: {proxy_ip}")

    browser = await p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage", 
            "--disable-web-security",
            "--no-sandbox",
            "--disable-infobars",
            "--window-position=0,0",
            "--start-maximized",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--proxy-bypass-list=<-loopback>",
            "--disable-ipc-flooding-protection"
        ],
        proxy={
            "server": f"http://{WEBSHARE_PROXY_CONFIG['hostname']}:{WEBSHARE_PROXY_CONFIG['port']}",
            "username": WEBSHARE_PROXY_CONFIG['username'],
            "password": WEBSHARE_PROXY_CONFIG['password']
        }
    )

    context = await browser.new_context(
        user_agent=user_agent,
        viewport={"width": random.randint(1280, 1366), "height": random.randint(720, 768)},
        locale='en-US',
        timezone_id=proxy_location["timezone"],
        geolocation={
            "latitude": proxy_location["latitude"],
            "longitude": proxy_location["longitude"]
        },
        permissions=["geolocation"],
        extra_http_headers={
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1", 
            "Accept-Language": "en-US,en;q=0.9"
        },
        ignore_https_errors=True
    )

    # Store full proxy info in context for later use
    context._proxy_info = proxy_location

    return p, browser, context
# ...existing code...