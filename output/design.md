# Campus Customs: Design Changes (Problem 10)

What we changed in the website's look and feel, and why. Inspiration: **yale.edu** (Yale Blue, white and gray, classic serif headlines, clean card grids) and **Aritzia's storefront** (image-first product grid, small uppercase labels, outlined filter buttons, minimal chrome). Aritzia's site blocks automated page fetches, so we worked from its well-known storefront patterns rather than its live code.

## Before Problem 10: rainbow → navy
The site launched (Problem 3) in the project's default **dark neon rainbow** style: red, orange, yellow, green, blue and indigo gradients on buttons, the logo and headline words. Because this is a **Yale** shop, we replaced the rainbow with **navy / Yale Blue** (`#00356b`) and lighter blues on the same dark background. Red, amber and green are kept only where they *mean* something (sold out, low stock, in stock). Why: rainbow read as a generic party theme. Navy is instantly "Yale" and looks more trustworthy for parents and alumni.

## Fonts
- **Headlines:** *Libre Caslon Text*, a classic serif close to Yale's own type. **Body/UI:** *Inter*. Inter had been declared in the CSS but was never actually loaded, so the browser was falling back to system fonts. Both now load from Google Fonts with `display=swap`.
- Accent words in headlines ("*Wear it loud.*") are serif italic instead of a gradient.
- **Why:** serif plus sans is the Yale look: academic and confident. One body font everywhere makes the UI calmer.

## Color
- Solid **Yale Blue** buttons, nav call to action, logo mark, chat header and user chat bubbles. Removed most neon glows, keeping soft shadows instead.
- One accent token (`--accent`) gives a lifted blue on dark and true Yale Blue on light, used for links, underlines and labels.
- Prices are now plain text (no glow), as on Aritzia.
- **Why:** fewer effects means the products stand out. Consistent blue tells shoppers what's clickable.

## Hierarchy
- Type scale: serif H1 up to 3.6 rem → serif H2 with a short blue rule under it → sans H3. Small **tracked uppercase labels** (0.2 em letter-spacing) for eyebrows, card categories and filter groups.
- Nav: an **underline that slides in** on hover and marks the active page (Yale style), replacing the glowing pills.
- Square-cornered (4 px) buttons and an outlined secondary button.
- **Why:** shoppers can scan the page (section, then product, then price) without reading everything.

## Product presentation (Aritzia-style)
- Cards lost their box. Each is an **image tile**, then a tiny uppercase category, then the name, a 2-line description, and a **price + color swatch dots** row.
- **Tile matches the photo:** each tile takes its background from the photo's own corner color, so photos shot on black sit on black and white shots on white, with no mismatched frames. The detail-page zoom frame does the same.
- Hover: the photo **zooms 6%** and a navy "**VIEW DETAILS →**" bar slides up.
- A "**LOW STOCK**" tag appears when 25 or fewer units are left in total (real inventory).
- Wider grid gaps (2.4 rem rows), and a detail page with a serif title, plain price and square size buttons.
- **Why:** big, consistent imagery sells apparel. Swatches and stock tags answer "what colors?" and "should I hurry?" without a click.

## Motion
- Each page **fades up** (0.45 s) on navigation. Product grids **reveal in a quick stagger** (40 ms apart).
- Hover zoom, sliding underlines, and a button **press** effect (scale 0.97).
- Chat: the launcher pops in, the panel scales up from the corner, bubbles slide in, and the typing dots bounce.
- One easing curve everywhere (`cubic-bezier(0.22, 1, 0.36, 1)`), so all motion feels like the same brand.
- **Everything turns off** for users with *prefers-reduced-motion*.
- **Why:** motion confirms actions and guides the eye. Respecting reduced motion keeps it accessible.

## Chat feel
- A **Handsome Dan bulldog avatar** on the launcher, the header and the assistant's messages (shown once per group of messages).
- Yale Blue header with a serif title and the guest / saved-chat status.
- **Quick-reply chips** before the first message: "Show me hoodies", "What's going fast?", "Gift ideas for Mom", "Navy gear under $60". On a product page they switch to "Do you have this in another color?", "Is my size in stock?" and "Show me similar items".
- Pill-shaped input and a round **↑** send button. Softer bubble shadows.
- **Why:** a face and one-tap starters make the assistant feel like a friendly shop helper, and get shoppers to their first useful answer faster.

## Checked
Headless-Chrome screenshots of Home, Products (dark and light, with filters), and a product page with a live chat show:
- serif headlines and underline nav;
- photo tiles that blend into their own backgrounds, with swatches and the hover "View details" bar;
- clicking a card still opens the product page;
- the avatar chat, where the quick reply "Do you have this in another color?" got "this hoodie comes in navy blue and white";
- no JavaScript errors.

**Known limit:** a few catalogue photos have a white image baked inside a black frame. That's in the image files themselves, so the tile can only match the outer black.
