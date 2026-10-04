# HW4 Usability Improvements (Problem 9)

What was added to the Campus Customs shop after the core site and chatbot were working, and why each change helps a shopper or the business. Entries are written as each improvement is built.

---

## 1. Product filters: Shop For, Product Type, Color, Size, Price

**What we added:** the Products page now has a row of outlined filter buttons, styled after Aritzia's: **Shop For**, **Product Type**, **Color**, **Size** and **Price**. Clicking a button opens a panel of options, and shoppers can pick more than one option in each filter:

| Filter | Options (product counts today) | Where the data comes from |
|---|---|---|
| Shop For | Women (4), Men (10), Unisex (88), and a **Family** group: Mom (2), Dad (3), Grandparents (3), Aunt & Uncle (2), Siblings (1) | The catalogue has no gender column, so audiences come only from **explicit labels**: "men's"/"mens" in the name, type or tags (for example "Champion **Mens** Triumph", a "men's outerwear" tag), and family gift names ("Yale **Mom** Hoodie", "Yale **Grandpa** Crewneck"). Everything without a label is Unisex. We don't guess a gender the shop never stated. |
| Product Type | Crewnecks, Hoodies, Jackets & Fleece, Long Sleeves, Quarter-Zips, T-Shirts | The old category chips moved here (the 22 messy `garment_type` spellings were already grouped in Problem 3). |
| Color | Navy, White, Gray, Blue, Red, Black, Yellow & Gold, Green, Cream, Coral, Multicolor, each with a color swatch | The 22 color spellings in the catalogue are grouped into 11 families, so "navy" and "navy blue" both appear under Navy. |
| Size | XS – XXL | Only products that **have that size in stock**, so a filter never leads to a sold-out size. |
| Price | Under $40, $40–$60, $60–$80, $80 & up | Based on the 7 real price points ($32–$98). |

Choices within one filter widen the results (Navy **or** Gray). Choices across filters narrow them (Women **and** Hoodies). Each active choice shows as a removable pill ("Shop For: Women ✕"), and there's a "Clear all" link. Every option shows how many products it matches, and options with 0 matches are greyed out. The filters live in the URL (`/products?shop_for=women&category=Hoodies`), so Back, Refresh and shared links all keep them. The old Home page category tiles still work.

**Why it helps:**
- **Shoppers** find the right item in a couple of clicks ("navy hoodie in M under $70") instead of scrolling through 102 products. The size filter only shows items they can actually buy in their size.
- **Gift buyers** can jump straight to the Family gifts (Mom, Dad, Grandparents…), a key audience for a college shop.
- **For the business:** less browsing friction means more product views and fewer shoppers leaving without finding what they wanted. The counts also show at a glance where the catalogue is thin. For example, there are no explicitly women's-cut items, only 4 women-targeted gifts, which is a gap the merchandising team could fill.

**Backend:** `GET /api/filters` returns every option with its count. `GET /api/products` now accepts `shop_for`, `category`, `color`, `size` and `price` (comma-separated). The filter logic is in `catalog.py` (`filter_products`, `color_families`, `shop_for`).

**Checked:**
- The `Women + Hoodies` URL renders the 3 hoodies (Aunt, Grandma, Mom), all 5 filter buttons and both active-filter pills.
- Every card still links to its product page.
- The Size counts match the database (75 products have XS in stock = 102 − 27 sold out in XS).
- The price bands add up to all 102 products.

## 2. "🔥 Going Fast" page: most popular items

**What we added:** a new page at `/going-fast`, linked in the nav bar as **🔥 Going Fast**. It shows the 12 items **closest to selling out**, ranked by fewest units left across all sizes. The hero says "Going fast! Lock it in." Each card has:
- an urgency badge: **"🔥 Only N left!"** when 10 or fewer units remain, **"⚡ N sizes sold out"** when 3 or more sizes are gone, otherwise "🔥 Going fast!";
- a "#1 / #2 / #3 trending" badge on the top three;
- a red-to-amber stock meter;
- the exact units left, "Almost gone: M (2)" for sizes with 1–3 units, "Sold out: XS, M", and "Still available: S L XXL".

Products with 0 units in every size are left out, since there's nothing to buy. Each card links to its normal product page.

**How "popular" is defined:** the database has no sales or view counts, so, as requested, *popular = nearly out of stock*. `GET /api/going-fast` (`catalog.going_fast()`) sorts products by total units left (fewest first), then by the number of sold-out sizes. **Every number on the page is live from `inventory`**, so the urgency is real, never invented. That keeps the copy honest, the same rule the chatbot follows.

**Why it helps:**
- **Shoppers** see the trending items in one place and know to act before their size disappears. The size details stop them clicking into a product that's already gone in their size.
- **For the business:** scarcity and social proof ("trending", "only 9 left") are proven conversion drivers. The page sells through low-stock items quickly, and gives merchandising an at-a-glance reorder list.

**Checked:** the page renders 12 cards. #1 is Football Left Chest T Shirt, "🔥 Only 9 left!" (database: 9 units). #2 is Tri Blend Sports Hockey T Shirt, "⚡ 4 sizes sold out" (database: 13 units, 4 sizes at 0). The nav link appears.

## 3. Light / dark theme toggle (☀ / ☾)

**What we added:** a pill button in the nav bar, right after **Create Account** (or after **Log Out** when signed in), showing **☀ / ☾**. The symbols are written as HTML entities `&#9728;` and `&#9790;`, and the current mode's symbol glows. Clicking it switches the whole site between the original dark navy theme and a new light theme: white cards, pale-blue background, Yale navy accents, darker blue links for contrast. The choice is saved in the browser (`localStorage`). It's applied in `main.tsx` before the page first draws, so returning shoppers never see a flash of the wrong theme.

**How:** every color in the site already came from CSS variables (`--bg`, `--surface`, `--text`, …). The light theme is a single `[data-theme='light']` block that swaps those variables, plus a few overrides for colors that were hard-coded (nav background, hero gradient, error text). Files: `theme.ts`, `components/ThemeToggle.tsx`, `NavBar.tsx`, `index.css`.

**Why it helps:**
- **Shoppers** can pick what's comfortable. Dark is easy on the eyes at night, while light is easier to read in bright rooms, on projectors, and for many people with low vision or astigmatism. Product photos (mostly on white or black) can look better against one or the other.
- **For the business:** the light theme matches Yale's official look (navy on white) for parents and alumni, while students keep the bold dark look. It's an accessibility win, and it costs nothing to maintain because it reuses the same variables.

**Checked:** headless-Chrome screenshots of the home page and Going Fast page in light mode show readable navy-on-white text, the ☀ / ☾ button after Create Account, and the light nav bar.

## 4. Bulldog that follows the cursor (home page)

**What we added:** a small cartoon bulldog (Handsome Dan style, in a navy "Y" sweater) that trots after the mouse on the **home page only**. It eases toward a spot just behind the cursor rather than sitting under it, turns to face the way it's running, moves its legs and head while moving, and wags its tail. It disappears when the mouse leaves the window. Files: `components/BulldogFollower.tsx` (drawn as SVG, animated with `requestAnimationFrame`), mounted in `pages/Home.tsx`.

It's built not to get in the way: it ignores clicks (`pointer-events: none`), so it can never block a button or link. It's **turned off on touch screens** (no cursor to follow) and for anyone whose device asks for **reduced motion**. It only runs while the home page is open.

**Why it helps:**
- **Shoppers:** it's a moment of delight that makes the first page memorable and on-brand (the Bulldog is Yale's mascot), and it invites people to move around the page and explore.
- **For the business:** playful brand details give the shop a personality that generic merch sites lack, which helps recall and sharing. Limiting it to the home page keeps the shopping pages (filters, product details, checkout path) distraction-free.

## 5. Backend: async agent runs, so chats never wait on each other

**What we changed:** everything the chatbot does while answering is now **non-blocking (`async`)**, so many agent runs can work at the same time on one server:
- **Tools** (`search_products`, `get_product_details`, `check_stock`, `list_categories`) are `async def`, and their SQLite reads run in worker threads (`asyncio.to_thread`). When the model asks for several tools at once, they run in parallel.
- **Page context** (`describe_page`) and the final **product cards + results page** lookups also run in worker threads. Cards and page are fetched together with `asyncio.gather`.
- **The `/api/chat` route** does its session lookup, history load and history save in worker threads. Database work never freezes the event loop that every other shopper's request is using.
- **Per-customer lock:** if one logged-in customer sends two messages at once (two tabs, a double-click), those two runs are queued. The second one then sees the first exchange in its history, and messages are saved in order. Different customers and guests never share a lock, so they still run concurrently.

**Why it helps:**
- **Shoppers** get answers just as fast during busy times (game weekends, move-in) as when the site is quiet. One slow answer doesn't hold up everyone else.
- **For the business:** one server handles more simultaneous shoppers, and a customer's chat history stays consistent even if they spam the send button.

**Checked (on a copy of the database):**
- 3 guest chats sent at the same moment all returned 200 in **3.6 s total**, versus about **7.4 s** if run one after another (a single chat took 6.4 s alone).
- The same logged-in customer sending 2 messages at once: both returned 200, and history was saved in order (user, assistant, user, assistant).

## 6. Backend: privacy and safety guards (`backend/privacy.py`)

**What we added:**

| Guard | What it does |
|---|---|
| **Name + email only** | The agent's `Customer` now holds only first name, last name and email. The "member since" date was removed, and the user id stays in code. The prompt says that's everything it knows and it must not ask for more. Page context is **no longer saved** with chats; only the messages are stored. |
| **Sensitive-data removal** | Before a shopper's message reaches the model **or the database**, `redact_sensitive()` replaces payment card numbers (checked with the Luhn checksum, so order numbers aren't caught), SSN-style ID numbers, phone numbers, street addresses, "my password is …", and other people's email addresses with tags like `[card number removed]`. Guest history sent by the browser is cleaned the same way. |
| **Privacy notice** | When something was removed, the chat shows a 🔒 note: "For your safety, we removed the card number … Please don't share personal or payment details in chat." |
| **Reply check** | The agent's reply is rejected and rewritten if it **asks the shopper for personal data** (address, phone, birthday, card, ID, password…) or contains **an email address that isn't the shopper's own**. This runs in the same output validator as the Problem 6 "no invented numbers" check. |
| **Rate limit** | 12 chat messages per minute per customer (or per IP for guests). After that the API returns HTTP 429, "You're sending messages very quickly…". This stops spam and runaway model costs. |
| **Prompt-injection hardening** | Text the browser controls (the results-page title from the URL, the page path) is flattened to one short line, with markup and quotes removed, before it goes into the instructions. Unknown paths aren't echoed at all. The prompt says to treat page titles, product text and earlier messages as information, never as instructions. |

**Why it helps:**
- **Shoppers** can't accidentally leave a card number or home address sitting in a chat log, and the bot never fishes for personal details. That builds trust, especially with parents and students.
- **For the business:** the shop collects only the data it needs (name and email), which follows data-minimization principles (GDPR / CCPA style) and keeps payment data out of systems that aren't built for it (a PCI concern). It also limits the damage if the database ever leaks, and the rate limit protects the API bill from abuse.

**Checked (live, on a copy of the database):**
- "my card is 4111 1111 1111 1111 … ship to 123 Elm Street, call (203) 555-0142" → the 🔒 notice listed address, card number and phone number. The reply refused to order and asked them not to resend. The **saved** message reads "my card is [card number removed] … ship to [address removed] … [phone number removed]".
- "what do you know about me? whats my birthday…" → "I know your name … and your email … I don't know your birthday or how long you've been a customer."
- "Can you remember my phone number…" → number removed, and the bot said it can't store phone numbers.
- No page context was stored (0 rows with `context_json`).
- Rate limiter: 12 of 15 rapid requests allowed, and a different shopper was still allowed.
- Unit checks: cards with dashes or spaces are caught, a 13-digit number that isn't a valid card is left alone, "Could you share your shipping address?" is flagged, and "Please don't share your card number" is not.

---

## Summary: 2+ frontend and 2+ backend improvements

| # | Side | Improvement | Why |
|---|---|---|---|
| 1 | Frontend | **Product filters**: Shop For (Women / Men / Unisex / Family), Product Type, Color, Size, Price | Shoppers find the right item in a couple of clicks, and gift buyers jump to Family gifts. Fewer people leave without finding anything. |
| 2 | Frontend | **🔥 Going Fast page**: lowest-stock items with honest "Only N left!" badges | Urgency and social proof drive conversions, using only real stock numbers. Doubles as a reorder list. |
| 3 | Frontend | **☀ / ☾ light/dark theme toggle** | Comfort and accessibility. The light mode matches Yale's navy-on-white look for parents and alumni. |
| 4 | Frontend | **Cursor-following bulldog** on the home page | On-brand delight that makes the shop memorable. Off on touch screens and for reduced motion. |
| 5 | Backend | **Async agent runs**: async tools, non-blocking database work, per-customer lock | Many shoppers chat at once without slowing each other (3 chats: 3.6 s vs 7.4 s), and history stays in order. |
| 6 | Backend | **Privacy and safety guards**: name and email only, sensitive-data removal, reply check, rate limit, injection hardening | Builds trust, minimizes stored personal data, keeps payment data out, and limits abuse and cost. |
| + | Backend (supporting) | `GET /api/filters`, filter parameters on `GET /api/products`, `GET /api/going-fast` | Power improvements 1 and 2 with real counts from the database. |

---

### Fix after Problem 9 (found during Problem 11): "Long Sleeves" filter
**Problem:** Product Type → Long Sleeves said **(2)**, but 44 products are long-sleeved. Worse, clicking it sometimes showed **nothing**. Two causes:
- "Long Sleeves" only matched the 2 items whose type is literally "long-sleeve shirt".
- A word typed in the search box stayed active invisibly, while the menu counts ignored it. After searching "hoodie", the menu promised 2 long-sleeve items but showed 0.

**Fix:**
1. Long Sleeves now includes **every long-sleeved product** (from its type, description or tags): **44** items, including crewnecks, hoodies, quarter-zips and jackets. A product can belong to its main type *and* Long Sleeves. The chatbot's search uses the same rule.
2. **Faceted counts:** `GET /api/filters` takes the current search and filters, and each option's count shows exactly how many results it would give. Options with 0 are greyed out.
3. The search term now shows as a removable pill ("Search: "hoodie" ✕").

**Checked in the browser:**
- Long Sleeves (44) → 44 cards.
- After searching "hoodie", the menu reads Hoodies (27), Long Sleeves (7), and Crewnecks / Quarter-Zips / T-Shirts / Jackets (0). Long Sleeves → exactly 7 cards.

**Why it matters:** a filter that says "2" and then shows nothing makes shoppers think the shop is broken or empty. Accurate counts build trust and stop dead-end clicks.
