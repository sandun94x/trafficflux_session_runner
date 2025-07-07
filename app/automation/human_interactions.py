import asyncio
import random
import json
import time
import math

async def log_mouse(x, y, log_list):
    log_list.append({"x": x, "y": y, "t": time.time()})

def minimum_jerk(t):
    return 10 * t**3 - 15 * t**4 + 6 * t**5

def sigmoid(t):
    return 1 / (1 + math.exp(-12 * (t - 0.5)))

def cubic_bezier(x0, x1, x2, x3, t):
    u = 1 - t
    return (
        u**3 * x0 + 3 * u**2 * t * x1 + 3 * u * t**2 * x2 + t**3 * x3
    )

def tremor(t, scale=1.0):
    # Natural micro-shaking with smooth bias
    return random.gauss(0, 0.3) * scale * math.sin(t * math.pi)

def generate_bezier_points(x0, y0, x1, y1, dist):
    angle = math.atan2(y1 - y0, x1 - x0)
    curvature_angle = math.radians(random.uniform(15, 40))  # larger deviation
    curviness = dist * random.uniform(0.25, 0.45)  # more pronounced curve

    # Randomize curve direction
    direction = random.choice([-1, 1])
    ctrl1 = (
        x0 + math.cos(angle + direction * curvature_angle) * curviness,
        y0 + math.sin(angle + direction * curvature_angle) * curviness
    )
    ctrl2 = (
        x1 + math.cos(angle - direction * curvature_angle) * curviness,
        y1 + math.sin(angle - direction * curvature_angle) * curviness
    )
    return ctrl1, ctrl2

async def human_move(page, position_state, x0, y0, x1, y1, log_list, steps=None):
    """
    Smooth, minimum jerk based Bezier mouse movement with micro-wobbles and tremors.
    """
    try:
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        steps = steps or int(min(max(dist / random.uniform(1.5, 2.5), 60), 220))

        x1 += random.gauss(0, 2.0)
        y1 += random.gauss(0, 2.0)

        ctrl1, ctrl2 = generate_bezier_points(x0, y0, x1, y1, dist)

        for i in range(steps):
            t_raw = i / (steps - 1)
            jerked_t = minimum_jerk(sigmoid(t_raw))

            x = cubic_bezier(x0, ctrl1[0], ctrl2[0], x1, jerked_t)
            y = cubic_bezier(y0, ctrl1[1], ctrl2[1], y1, jerked_t)

            phase = t_raw * math.pi * 2
            x += math.sin(phase + random.random()) * (1 + random.random() * 1.2)
            y += math.cos(phase + random.random()) * (1 + random.random() * 1.2)

            x += tremor(t_raw, scale=1.0)
            y += tremor(t_raw, scale=1.0)

            await page.mouse.move(x, y)
            await log_mouse(x, y, log_list)
            await asyncio.sleep(random.uniform(0.008, 0.016))

            if i % random.randint(12, 20) == 0 and i > steps // 5:
                await asyncio.sleep(random.uniform(0.02, 0.05))

        await simulate_cursor_hover_cluster(page, x1, y1, radius=random.uniform(1.5, 3.5))
        await micro_adjustment_wiggle(page, x1, y1, log_list, jitter=2.0, count=random.randint(3, 6))

        position_state["x"], position_state["y"] = x1, y1

    except Exception as e:
        print(f"Error in human_move: {e}")

async def micro_adjustment_wiggle(page, x, y, log_list, jitter=2.0, count=4):
    for _ in range(count):
        offset_x = random.gauss(0, jitter)
        offset_y = random.gauss(0, jitter)
        await page.mouse.move(x + offset_x, y + offset_y)
        await log_mouse(x + offset_x, y + offset_y, log_list)
        await asyncio.sleep(random.uniform(0.03, 0.08))

async def simulate_cursor_hover_cluster(page, x_center, y_center, radius=2.5, count=6):
    for i in range(count):
        angle = random.uniform(0, 2 * math.pi)
        r = radius + random.uniform(-1.2, 1.2)
        x = x_center + r * math.cos(angle)
        y = y_center + r * math.sin(angle)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.05, 0.14))

async def hover_idle_before_click(page, position_state, x, y, log_list):
    await human_move(page, position_state, position_state['x'], position_state['y'], x, y, log_list)
    await micro_adjustment_wiggle(page, x, y, log_list)
    await simulate_cursor_hover_cluster(page, x, y, radius=2.5, count=random.randint(4, 7))
    await asyncio.sleep(random.uniform(0.3, 0.6))

async def initialize_mouse(page, position_state, log_list):
    viewport = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
    x = random.randint(100, viewport["width"] - 100)
    y = random.randint(100, viewport["height"] - 100)
    await page.mouse.move(x, y)
    await log_mouse(x, y, log_list)
    position_state["x"] = x
    position_state["y"] = y

async def move_cursor_to_element(page, selector, position_state, log_list, offset_range=10):
    try:
        element = page.locator(selector).first
        box = await element.bounding_box()
        if box:
            x1 = box["x"] + box["width"] / 2 + random.uniform(-offset_range, offset_range)
            y1 = box["y"] + box["height"] / 2 + random.uniform(-offset_range, offset_range)
            x0, y0 = position_state["x"], position_state["y"]
            await human_move(page, position_state, x0, y0, x1, y1, log_list)
            await micro_adjustment_wiggle(page, x1, y1, log_list)
            return True
        return False
    except Exception as e:
        print(f"Error in move_cursor_to_element: {e}")
        return False

async def random_mouse_play(page, position_state, log_list):
    try:
        viewport = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
        x0, y0 = position_state["x"], position_state["y"]

        for _ in range(random.randint(2, 5)):
            x1 = random.randint(100, viewport['width'] - 100)
            y1 = random.randint(100, viewport['height'] - 100)
            await human_move(page, position_state, x0, y0, x1, y1, log_list)
            await micro_adjustment_wiggle(page, x1, y1, log_list)

            x0, y0 = x1, y1
            await asyncio.sleep(random.uniform(0.3, 0.8))

    except Exception as e:
        print(f"Error in random_mouse_play: {e}")

async def spontaneous_mouse_wander(page, position_state, log_list):
    try:
        viewport = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
        x0, y0 = position_state["x"], position_state["y"]

        for _ in range(random.randint(2, 4)):
            x1 = random.randint(50, viewport["width"] - 50)
            y1 = random.randint(50, viewport["height"] - 50)
            await human_move(page, position_state, x0, y0, x1, y1, log_list)
            await micro_adjustment_wiggle(page, x1, y1, log_list)

            x0, y0 = x1, y1
            await asyncio.sleep(random.uniform(0.2, 0.5))
    except Exception as e:
        print(f"Error in spontaneous_mouse_wander: {e}")

async def human_like_typing(page, selector, text):
    try:
        await page.fill(selector, "")
        await asyncio.sleep(random.uniform(0.2, 0.5))

        typo_chance = 0.15
        corrected_text = ""

        for i, char in enumerate(text):
            # Randomly making a typo
            if random.random() < typo_chance and char.isalnum():
                typo = random.choice("abcdefghijklmnopqrstuvwxyz")
                await page.type(selector, typo, delay=random.uniform(100, 250))
                await asyncio.sleep(random.uniform(0.2, 0.4))
                await page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.1, 0.3))

            await page.type(selector, char, delay=random.uniform(80, 180))
            corrected_text += char

            # thinking pause
            if random.random() < 0.1:
                await asyncio.sleep(random.uniform(0.4, 1.0))

    except Exception as e:
        print(f"Error in human_like_typing: {e}")

async def human_scroll(page):
    try:
        total_scroll = 0
        max_scrolls = random.randint(3, 6)
        for _ in range(max_scrolls):
            scroll_delta = random.randint(100, 400)
            direction = random.choice([-1, 1])
            await page.evaluate(f"window.scrollBy({{ top: {direction * scroll_delta}, behavior: 'smooth' }});")
            await asyncio.sleep(random.uniform(0.6, 1.5))
            total_scroll += scroll_delta
    except Exception as e:
        print(f"Error in human_scroll: {e}")

async def random_human_sequence(page):
    try:
        actions = [human_scroll, random_mouse_play, spontaneous_mouse_wander]
        selected_action = random.choice(actions)
        await selected_action(page)
        await asyncio.sleep(random.uniform(0.5, 1.2))
    except Exception as e:
        print(f"Error in random_human_sequence: {e}")

async def simulate_reading_pattern(page, position_state, log_list, start_y=200, row_spacing_range=(60, 100), columns=2):
    try:
        viewport = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
        left_x = random.randint(120, 250)
        right_x = min(viewport["width"] - 100, left_x + random.randint(150, 250))

        for i in range(random.randint(3, 6)):
            y = start_y + i * random.randint(*row_spacing_range)
            x = right_x if i % columns else left_x

            await human_move(page, position_state, position_state["x"], position_state["y"], x, y, log_list)
            await micro_adjustment_wiggle(page, x, y, log_list)
            await asyncio.sleep(random.uniform(0.4, 0.9))

    except Exception as e:
        print(f"simulate_reading_pattern failed: {e}")

async def handle_cookie_consent(page):
    try:
        await asyncio.sleep(random.uniform(1.0, 2.0))  # simulate human delay

        buttons = await page.query_selector_all("button")

        for btn in buttons:
            try:
                text = await btn.evaluate("el => el.innerText.toLowerCase().trim()")
                if any(keyword in text for keyword in ["reject all", "reject", "decline", "don't accept", "do not accept"]):
                    box = await btn.bounding_box()
                    if box:
                        x = box["x"] + box["width"] / 2
                        y = box["y"] + box["height"] / 2

                        # Move cursor to the button
                        position_state = {"x": 640, "y": 360}
                        mouse_log = []
                        await human_move(page, position_state, position_state["x"], position_state["y"], x, y, mouse_log)
                        await micro_adjustment_wiggle(page, x, y, mouse_log)
                    
                    await btn.click()
                    print("Cookie rejection handled")
                    await asyncio.sleep(random.uniform(1.5, 2.5))
                    return True
            except:
                continue

        # Check if a cookie-related button likely exists first
        cookie_keywords = ["cookie", "privacy", "consent"]
        popup_text = await page.content()

        if any(k in popup_text.lower() for k in cookie_keywords):
            print("No matching reject button found in possible cookie popup.")
        else:
            print("No cookie popup detected.")

        return False

    except Exception as e:
        print(f"Cookie handling failed: {e}")
        return False
