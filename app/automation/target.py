import asyncio
import random
import json
import os
from app.automation.human_interactions import *
from app.automation.IP_rotation import *

# Configuration
CONFIG = {
    "mode": os.getenv("AUTOMATION_MODE", "stealth"),
    "long_wait_time": lambda: random.uniform(300, 600) if os.getenv("AUTOMATION_MODE") == "stealth" else random.uniform(10, 20),
    "headless": os.getenv("HEADLESS", "false").lower() == "true",
}

async def prepare_page(page, user_agent, proxy_ip="127.0.0.1"):
    """Prepare page with fingerprint spoofing"""
    # This is now redundant since create_new_page handles fingerprinting
    # Just add a small delay for readiness
    await asyncio.sleep(random.uniform(0.5, 1.0))
    print("[INFO] Page prepared successfully")

async def detect_recaptcha(page):
    """Detect reCAPTCHA or CAPTCHA elements on the page"""
    try:
        await asyncio.sleep(1)
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            ".g-recaptcha",
            "#captcha",
            ".captcha",
            "iframe[title*='reCAPTCHA']"
        ]
        
        for selector in captcha_selectors:
            element = await page.query_selector(selector)
            if element:
                print(f"CAPTCHA detected: {selector}")
                return True
        return False
    except Exception as e:
        print(f"Error detecting CAPTCHA: {e}")
        return False

async def find_google_search_input(page):
    """Find the Google search input field"""
    selectors = [
        'input[name="q"]',
        'input[title="Search"]',
        'input[type="text"][aria-label*="Search"]',
        'textarea[name="q"]'
    ]
    
    for selector in selectors:
        try:
            element = await page.query_selector(selector)
            if element and await element.is_visible():
                return selector
        except:
            continue
    return None

async def find_target_links(page, domain, position_state, log_list, max_pages=5):
    """Find links to target domain on Google search results"""
    try:
        for page_num in range(max_pages):
            print(f"🔍 Checking Google result page {page_num + 1}")

            await human_scroll(page)
            await random_mouse_play(page, position_state, log_list)
            await asyncio.sleep(random.uniform(2.5, 4.5))

            domain_keywords = domain.replace("https://", "").replace("http://", "").replace("www.", "")
            base = domain_keywords.split("/")[0]
            
            # Debug: Show what we're searching for
            print(f"🔍 Searching for domain: {base}")

            target_selectors = [
                f'a[href*="{base}"]',
                f'div[data-href*="{base}"]',
                f'div:has(a[href*="{base}"])'
            ]

            found_links = []

            for selector in target_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"🎯 Selector '{selector}' found {len(elements)} elements")
                    
                    for element in elements:
                        href = await element.get_attribute('href')
                        if not href:
                            try:
                                link_handle = await element.query_selector('a[href]')
                                if link_handle:
                                    href = await link_handle.get_attribute('href')
                                    element = link_handle
                            except:
                                continue

                        if href and base in href:
                            try:
                                if await element.is_visible():
                                    box = await element.bounding_box()
                                    if box:
                                        found_links.append({
                                            'element': element,
                                            'href': href
                                        })
                                        print(f"✅ Found target link: {href}")
                                        # Don't return immediately - search all pages first
                            except Exception as link_error:
                                print(f"Error checking link visibility: {link_error}")
                                continue
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue

            if found_links:
                print(f"🎯 Found {len(found_links)} links on page {page_num + 1}")
                return found_links

            # Try pagination - improved Next button selectors
            if page_num < max_pages - 1:
                try:
                    # Multiple selectors for Next button based on your HTML structure
                    next_selectors = [
                        'a[aria-label="Next"]',
                        'a[id="pnnext"]',
                        'span[class*="oe"]:has-text("Next")',
                        'a:has-text("Next")',
                        'td[class*="d6cvqb"] a[aria-label="Next"]',
                        'a[href*="start="]'  # Generic pagination link
                    ]
                    
                    next_button = None
                    for next_sel in next_selectors:
                        try:
                            next_button = await page.query_selector(next_sel)
                            if next_button and await next_button.is_visible():
                                print(f"🔍 Found Next button with selector: {next_sel}")
                                break
                        except:
                            continue
                    
                    if next_button and await next_button.is_visible():
                        print(f"🔄 Moving to page {page_num + 2}")
                        await next_button.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                        
                        # Move cursor to Next button with human-like movement
                        box = await next_button.bounding_box()
                        if box:
                            x = box["x"] + box["width"] / 2
                            y = box["y"] + box["height"] / 2
                            await human_move(page, position_state, position_state["x"], position_state["y"], x, y, log_list)
                            await micro_adjustment_wiggle(page, x, y, log_list)
                        
                        await next_button.hover(timeout=3000)
                        await asyncio.sleep(random.uniform(0.5, 1.2))
                        await next_button.click()
                        
                        # Wait for new page to load
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        await asyncio.sleep(random.uniform(2.0, 3.5))
                        print(f"✅ Successfully navigated to page {page_num + 2}")
                    else:
                        print("❌ No 'Next' button found — stopping pagination")
                        break
                except Exception as e:
                    print(f"❌ Next page navigation error: {e}")
                    break

        print(f"❌ No links to {domain} found after searching {max_pages} page(s)")
        return []

    except Exception as e:
        print(f"❌ Fatal error in find_target_links: {e}")
        return []

async def interact_with_target_site(page, position_state, log_list):
    """Interact with the target website in a human-like manner"""
    try:
        print("🎯 Interacting with target site...")
        await page.wait_for_load_state('domcontentloaded', timeout=15000)
        await asyncio.sleep(random.uniform(3.0, 5.0))
        
        # Add page reload AFTER successfully loading the target site
        print("🔄 Reloading target page...")
        await page.reload(wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(random.uniform(3.0, 5.0))
        print("✅ Target page reloaded successfully")
        
        # Reset mouse position and perform initial movements
        position_state["x"] = random.randint(300, 700)
        position_state["y"] = random.randint(200, 400)
        await page.mouse.move(position_state["x"], position_state["y"])
        
        # Perform human-like scrolling and mouse movements
        await human_scroll(page)
        await asyncio.sleep(random.uniform(2.0, 4.0))
        await random_mouse_play(page, position_state, log_list)
        await asyncio.sleep(random.uniform(2.0, 3.0))
        
        # Simulate reading behavior
        await simulate_reading_pattern(page, position_state, log_list)
        await asyncio.sleep(random.uniform(3.0, 5.0))

        # Try to find and interact with clickable elements
        potential_clicks = [
            'a[href*="product"]', 'a[href*="review"]', 'a[href*="category"]',
            'button:has-text("View")', 'button:has-text("Read")', 'button:has-text("More")',
            '.product-link', '.review-link', '.category-link',
            'a:has-text("Review")', 'a:has-text("Product")', 'a:has-text("More")',
            'nav a', '.menu a', '.navigation a'
        ]

        clicked_element = False
        for selector in potential_clicks:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    # Filter for visible elements
                    visible_elements = []
                    for element in elements[:5]:  # Check first 5 elements
                        try:
                            if await element.is_visible():
                                box = await element.bounding_box()
                                if box and box["width"] > 0 and box["height"] > 0:
                                    visible_elements.append(element)
                        except:
                            continue
                    
                    if visible_elements:
                        element = random.choice(visible_elements)
                        box = await element.bounding_box()
                        if box:
                            x = box["x"] + box["width"] / 2
                            y = box["y"] + box["height"] / 2
                            
                            # Scroll element into view first
                            await element.scroll_into_view_if_needed()
                            await asyncio.sleep(random.uniform(1.0, 2.0))
                            
                            # Move to element with human-like movement
                            await human_move(page, position_state, position_state["x"], position_state["y"], x, y, log_list)
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                            
                            # Add hover effect and micro adjustments
                            await micro_adjustment_wiggle(page, x, y, log_list)
                            await simulate_cursor_hover_cluster(page, x, y)
                            await asyncio.sleep(random.uniform(0.3, 0.8))
                            
                            # Click the element
                            await element.click()
                            print(f"✅ Successfully clicked element with selector: {selector}")
                            
                            # Wait for page to load and interact more
                            await page.wait_for_load_state('domcontentloaded', timeout=10000)
                            await asyncio.sleep(random.uniform(3.0, 6.0))
                            
                            # Continue interacting on the new page
                            await random_mouse_play(page, position_state, log_list)
                            await human_scroll(page)
                            
                            clicked_element = True
                            break
            except Exception as e:
                print(f"Error trying selector {selector}: {e}")
                continue

        if not clicked_element:
            print("🎯 No clickable elements found, performing general interactions...")
            # Perform more scrolling and mouse movements
            for _ in range(3):
                await human_scroll(page)
                await asyncio.sleep(random.uniform(2.0, 4.0))
                await random_mouse_play(page, position_state, log_list)
                await asyncio.sleep(random.uniform(1.5, 3.0))

        # Final interaction phase
        await asyncio.sleep(random.uniform(5.0, 10.0))
        await random_mouse_play(page, position_state, log_list)
        print("✅ Target site interaction completed")

    except Exception as e:
        print(f"Failed interaction with target site: {e}")
        # Even if there's an error, try to do some basic interactions
        try:
            await human_scroll(page)
            await random_mouse_play(page, position_state, log_list)
        except:
            pass

async def handle_noise_tab(context, keyword, tab_id, user_agent, click_links=False):
    """Handle noise tab creation and interaction"""
    page = None
    try:
        # Fix: Get proxy_info from context as dictionary
        proxy_info = getattr(context, '_proxy_info', {'ip': '127.0.0.1', 'timezone': 'America/New_York'})
        page = await create_new_page(context, user_agent, proxy_info)
        print(f"[Tab {tab_id}] Using UA: {user_agent[:50]}...") 
        print(f"[Tab {tab_id}] Searching: {keyword}")
        await page.goto("https://www.google.com/ncr", timeout=15000)
        await asyncio.sleep(random.uniform(3.0, 5.0))

        position_state = {"x": 640, "y": 360}
        mouse_log = []

        await initialize_mouse(page, position_state, mouse_log)
        await handle_cookie_consent(page)

        selector = await find_google_search_input(page)
        if not selector:
            print(f"[Tab {tab_id}] No input box found")
            return

        await move_cursor_to_element(page, selector, position_state, mouse_log)
        await human_like_typing(page, selector, keyword)
        await page.keyboard.press("Enter")

        try:
            await page.wait_for_selector("#search, #rso", timeout=10000)
        except:
            print(f"[Tab {tab_id}] Search results didn't load.")
            return

        await asyncio.sleep(random.uniform(2.0, 4.0))
        await random_mouse_play(page, position_state, mouse_log)
        await human_scroll(page)

        if click_links:
            # Simulate some interactions
            action_choice = random.choices(
                ["top_tab", "result_link", "linger"],
                weights=[4, 4, 2],
                k=1
            )[0]

            if action_choice == "top_tab":
                print(f"[Tab {tab_id}] Clicking a top nav category")
                nav_selectors = [
                    'a:has-text("Images")',
                    'a:has-text("Videos")',
                    'a:has-text("News")',
                    'a:has-text("Web")',
                    'a:has-text("Forums")'
                ]
                random.shuffle(nav_selectors)

                for nav_sel in nav_selectors:
                    try:
                        nav_element = await page.query_selector(nav_sel)
                        if nav_element and await nav_element.is_visible():
                            await nav_element.click()
                            await page.wait_for_load_state('domcontentloaded', timeout=8000)
                            await asyncio.sleep(random.uniform(2.0, 4.0))
                            break
                    except:
                        continue

        await asyncio.sleep(random.uniform(3.0, 8.0))
        print(f"[Tab {tab_id}] Closed")

    except Exception as e:
        print(f"[Tab {tab_id}] Error: {e}")
    finally:
        if page:
            try:
                await page.close()
            except:
                pass

async def simulate_noise_tabs(context, base_keyword, user_agent):
    """Simulate noise tabs to appear more human-like"""
    noise_keywords = [
        f"{base_keyword} review",
        f"{base_keyword} price",
        f"best {base_keyword}",
        f"{base_keyword} comparison",
        f"how to use {base_keyword}",
        "weather today",
        "news headlines",
        "stock market",
        "sports scores"
    ]
    
    selected_keywords = random.sample(noise_keywords, random.randint(2, 4))
    
    tasks = []
    for i, keyword in enumerate(selected_keywords):
        task = asyncio.create_task(
            handle_noise_tab(context, keyword, i+1, user_agent, click_links=random.choice([True, False]))
        )
        tasks.append(task)
        await asyncio.sleep(random.uniform(5.0, 8.0))
    
    await asyncio.gather(*tasks, return_exceptions=True)


async def single_session_run(keyword, target_domain, stop_flag=None):
    """Main function to run the traffic automation - runs once per call"""
    search_keyword = keyword
    target_domain = target_domain

    if not search_keyword or not target_domain:
        print("Keyword or domain missing. Exiting.")
        return

    session_user_agent = get_random_user_agent()
    
    # Initialize these at function level for proper cleanup
    p = None
    browser = None
    context = None
    main_page = None
    
    try:
        # Check stop flag before starting session
        if stop_flag and stop_flag.is_set():
            print("🛑 Stop signal received. Gracefully shutting down...")
            return
        
        p, browser, context = await launch_stealth_browser(session_user_agent)

        captcha_retries = 0
        max_captcha_retries = 3
        session_success = False

        while captcha_retries < max_captcha_retries and not session_success:
            # Check stop flag during session attempts
            if stop_flag and stop_flag.is_set():
                print("🛑 Stop signal received during session. Gracefully shutting down...")
                return
                
            try:
                # Fix: Get proxy_info from context as dictionary instead of just IP
                proxy_info = getattr(context, '_proxy_info', {'ip': '127.0.0.1', 'timezone': 'America/New_York'})
                main_page = await create_new_page(context, session_user_agent, proxy_info)
                
                position_state_main = {"x": 640, "y": 360}
                mouse_log_main = []

                print("🚀 Navigating to Google...")
                await main_page.goto("https://www.google.com/ncr", timeout=20000)
                await initialize_mouse(main_page, position_state_main, mouse_log_main)
                await handle_cookie_consent(main_page)

                selector = await find_google_search_input(main_page)
                if not selector:
                    print("❌ No Google search input found")
                    continue

                await move_cursor_to_element(main_page, selector, position_state_main, mouse_log_main)
                await human_like_typing(main_page, selector, search_keyword)
                await main_page.keyboard.press("Enter")

                try:
                    await main_page.wait_for_selector("#search, #rso", timeout=10000)
                    print("✅ Search results loaded")
                except:
                    if await detect_recaptcha(main_page):
                        print("🤖 CAPTCHA detected — sleeping to reduce fingerprint flagging.")
                        # Check stop flag during long wait
                        for _ in range(int(CONFIG["long_wait_time"]())):
                            if stop_flag and stop_flag.is_set():
                                print("🛑 Stop signal received during CAPTCHA wait. Gracefully shutting down...")
                                return
                            await asyncio.sleep(1)
                        captcha_retries += 1
                        continue
                    else:
                        print("❌ Search results failed to load")
                        continue

                await asyncio.sleep(random.uniform(5.0, 10.0))
                await random_mouse_play(main_page, position_state_main, mouse_log_main)
                await simulate_reading_pattern(main_page, position_state_main, mouse_log_main)

                links = await find_target_links(main_page, target_domain, position_state_main, mouse_log_main, max_pages=5)
                await asyncio.sleep(random.uniform(2.0, 4.0))

                if links:
                    print(f"🎯 Found {len(links)} target link(s)")
                    for i, selected in enumerate(links):
                        # Check stop flag before each link interaction
                        if stop_flag and stop_flag.is_set():
                            print("🛑 Stop signal received during link interaction. Gracefully shutting down...")
                            return
                            
                        try:
                            print(f"🖱 Attempting to click link {i+1}: {selected.get('href', 'Unknown URL')}")
                            element_handle = selected['element']
                            tag_name = await element_handle.evaluate("el => el.tagName.toLowerCase()")

                            if tag_name != 'a':
                                anchor = await element_handle.evaluate_handle("el => el.closest('a')")
                                element_handle = anchor.as_element() if anchor else None
                                if not element_handle:
                                    continue

                            if element_handle:
                                await element_handle.scroll_into_view_if_needed()
                                if not await element_handle.is_visible():
                                    continue

                                box = await element_handle.bounding_box()
                                if not box:
                                    continue

                                x = box["x"] + box["width"] / 2
                                y = box["y"] + box["height"] / 2
                                await human_move(main_page, position_state_main, position_state_main["x"], position_state_main["y"], x, y, mouse_log_main)
                                await simulate_cursor_hover_cluster(main_page, x, y)
                                await asyncio.sleep(random.uniform(0.2, 0.5))

                                await element_handle.click()
                                print("✅ Successfully clicked target link")
                                await main_page.wait_for_load_state('domcontentloaded', timeout=10000)
                                await asyncio.sleep(random.uniform(2.0, 3.0))

                                if await detect_recaptcha(main_page):
                                    print("🤖 CAPTCHA detected after clicking — cooling off.")
                                    # Check stop flag during long wait
                                    for _ in range(int(CONFIG["long_wait_time"]())):
                                        if stop_flag and stop_flag.is_set():
                                            print("🛑 Stop signal received during CAPTCHA wait. Gracefully shutting down...")
                                            return
                                        await asyncio.sleep(1)
                                    captcha_retries += 1
                                    break
                                else:
                                    await handle_cookie_consent(main_page)
                                    await interact_with_target_site(main_page, position_state_main, mouse_log_main)
                                    session_success = True
                                    break

                        except Exception as e:
                            print(f"❌ Error interacting with link: {e}")
                            continue
                else:
                    print(f"❌ No links found for domain: {target_domain}")
                    session_success = True  # Consider it successful even without links

                # Run noise tabs if session was successful
                if session_success:
                    print("🎭 Creating noise tabs...")
                    await simulate_noise_tabs(context, search_keyword, session_user_agent)  
                    print("✅ Session automation complete.")

                    # Save mouse log
                    with open("mouse_log.json", "w") as f:
                        json.dump(mouse_log_main, f, indent=2)

            except Exception as e:
                print(f"❌ Unexpected error in session loop: {e}")
                captcha_retries += 1
            finally:
                # Close main page after each attempt
                if main_page:
                    try:
                        await main_page.close()
                    except:
                        pass

        # Final status message
        if captcha_retries >= max_captcha_retries and not session_success:
            print("❌ Max captcha retries reached for current session.")
        else:
            print("✅ Session completed successfully.")

    except KeyboardInterrupt:
        print("🛑 Script interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error in main session: {e}")
    finally:
        # ✅ Proper cleanup to prevent EPIPE error
        print("🧹 Cleaning up current session...")
        
        if main_page:
            try:
                await main_page.close()
            except Exception as cleanup_error:
                print(f"Page cleanup error (can be ignored): {cleanup_error}")
        
        if context:
            try:
                await context.close()
            except Exception as cleanup_error:
                print(f"Context cleanup error (can be ignored): {cleanup_error}")
        
        if browser:
            try:
                await browser.close()
            except Exception as cleanup_error:
                print(f"Browser cleanup error (can be ignored): {cleanup_error}")
        
        if p:
            try:
                await p.stop()
            except Exception as cleanup_error:
                print(f"Playwright cleanup error (can be ignored): {cleanup_error}")

    print("🏁 Single session automation completed.")

# if __name__ == "__main__":
#     asyncio.run(single_session_run("precision mechanical keyboard-kb1001","https://test.verdic.ai/products/keyboard.html"))