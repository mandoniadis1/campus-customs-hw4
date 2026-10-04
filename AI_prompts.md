# AI Prompt Log

All prompts are verbatim, in the order they were typed, grouped by problem.

## Problem 1 - Setup

> /AI_prompts hw4

> unzip data (2).zip in my downloads folder and put the contents in hw4

## Problem 2 - Analyze the database

> Ok we're on Problem 2: Analyze the database
>
> Background on this hw4: we're creating a website for Campus Customs with a chatbot for customers to use.
>
> Look at the sql database campus_customs that we just unzipped. Analyze so you understand catalogue, inventory, and users.
>
> To do this next part first make an agent for this since it's getting competitive. Run it afterwards. Make an agent called by forward slash harness that does exactly what harness.md did in hw3. So it starts the file output/harness.md here in hw4 and we'll add to it as we go along. Command will be /harness and anything I'm adding to the md file. If the .md doesn't exist yet in the folder we're working in create it. So when you run it here it will be /harness write down each table and the table fields and one short line on why each field matters for the shop/chatbot.
>
> Ok so analyze the database and put it into a new harness using newly created agent as specified above.

## Problem 3 - Build the Campus Customs website

> Moving on to Problem 3: Build the Campus Customs website
>
> Scaffold a React + Vite + Typescript front end. Put a nav bar at the top linking the pages Home/Products/About Us/Log In/Create Account
>
> For the home and about us page, pull your themed wording (WITHOUT COPYING THE TEXT) from https://yalebulldogblue.com/
>
> On the products page show the product images from the catalogue with the basic product info (name/price/short description)
>
> Clicking on a product should take the shopper to the single-item page with more info on that product (large image on one side with zoom feature, full product text on the right side with description/price/size/stock)
>
> Also add a chat interface on the bottom right (floating chat panel). It doesn't need to be connected to an agent yet (we'll do that later)
>
> As an aside: We'll need a small API soon to read the database. We can start with FastAPI app in backend/main.py to serve products and images for now, and we'll grow it into the agent in problem 5
>
> Ok Start

## Problem 4 - Create account and login

> Moving on to Problem 4: Create account and login
>
> Make a create account form (first name, last name, email, password, confirm password)
>
> and the login is email and pw
>
> Log all users into the users table. Make sure pws are stored securely so hackers can't reach them
>
> The seed db has a test user I will use to test this works as well as creating an account to see if it works
>
> Then /harness how auth works (what you store for a user and how pws are protected)

> continue

## Problem 5 - PydanticAI agent backend

> Moving on to problem 5: PydanticAI agent backend. Build the chatbot for the shop using pydanticAI behind FastAPI and plugged into the frontend chat widget. Put the API app in backend/main.py (the file we run with Uvicorn). Keep the agent as these 4 files next to it: 
> backend/prompts/prompt.md - system prompt to grow later. Put the Campus Customs voice and safety basics here as well. 
> backend/agent.py - agent entry/wiring
> backend/tools.py - tools for the agent
> backend/models.py - PydanticAI structured types. Start or update types here for chat replies and product cards as needed
>
> Expose the chat routes in main.py so a message from the site returns an agent reply. API key will be needed. 
>
> Then /harness note how the frontend talks to FastAPI and how the agent is loaded (prompt file + model)
>
> Make sure the backend runs from backend/ folder like this:
> uvicorn main:app --reload --port 8000
>
> OK GO

## Problem 6 - Tools: Product info and stock

> Moving on to problem 6: Tools: Product info and stock. 
>
> Give the agent tools so it can look up real information from the campus_customs.db (product description, price, how many in stock by size). DO NOT INVENT PRICES OR QUANTITIES. IF A SIZE IS OUT OF STOCK SAY SO CLEARLY. Put this as an expansion in the prompts/prompt.md so the agent knows to call these tools. Add/update any return types in models.py
>
> Then /harness list each tool and explain which model fields were chosen for lookup results and why
>
> OK GO

## Problem 7 - Chat search that updates the page

> Moving on to problem 7: chat search that updates the page
>
> like what the problem says ^. when a customer asks the chatbot for a particular item / type of item, the agent searches the catalogue and dynamically pulls that website page up for customer viewing, showing the matching items as product cards. (image, name, price, short info). After the dynamic cards are loaded by this new feature, make sure the same single-item page behavior built in problem 3 still works (each card should still open the detailed view when clicked). Then update prompts/prompt.md and /harness make it clear how search results reach the page with this new API contract feature.

## Problem 8 - Customer memory

> Moving on to problem 8: customer memory. 
>
> For a logged in customer, save their chat history in the db in an appropriate table and reload it when they log back in. The agent must know who's logged in (name, email). Put that in agent deps (or an equivalent clear pattern) or tools the agent can call. Make sure the agent can also understand enough context so that if the custome is on a page with a navy hoodie and asks "do you have it in pink?" the agent can understand what "it" refers to. This can be coded. 
>
> Guests don't get chat history, only those with accounts that log in. 
>
> /harness how chat history is stored, what customer fields the agent can see, and how the page context is passed
>
> OK GO

## Problem 9 - Usability improvements

> Moving on to problem 9: usability improvements
>
> We have the core shop down now so let's improve it. 
>
> Frontend:
> 1. add a button next to the create account button that can change the theme from dark to light. Show a sun, forward slash, and moon (html format).
> 2. Make a little bulldog follow the cursor around on the main page.
> 3. Make a page of most popular items. These are items that are close to out of stock. Can put "Going fast!" and other things on the page to let customers know that these are the trendy items that they need to lock down fast. 
> 4. On the products page, we need more filters. Like the screenshot attached from the Aritizia website. Clicking on each filter shows diffferent options (like opening color filter shows different color options to click on). Include a "Shop For" filter that shops for women vs men and other subcats if the db has anything else. The filters we have now (crewnecks, hoodies, etc) will go under "Product Type" filter
>
> backend
> 1. Make sure if multiple agents are going at once for a customer request that async is used. 
> 2. Make sure the agent doesn't gather any information about the customer beyond name and email. Add any other safety features deemed necessary and log in prompts and /harness safety
>
> OK GO
>
> [Image attached: screenshot of Aritzia filter buttons "Color", "Size", "Product Type"]

> Write in output/usability.md as you build each of the improvements. Say what you added and why it helps a shopper or the business

> Also I need 2 front end and 2 backend improvements for this problem so make sure at least 2 of each are being implemented, what they are and why

## Problem 10 - Style the website

> Moving on to problem 10: style the website
>
> I know we've already did a lot of styling but we need to style more for points (fonts, color, hierarchy, motion, product presentation, chat feel)
>
> Write output/design.md what we changed and why (keep short and concrete)
>
> Can use https://www.yale.edu/ the yale website for inspo and https://www.aritzia.com/us/en/clothing/accessories/socks?lastViewed=43
> The artizia storefront. 
>
> Include that we changed it already from rainbow to navy in the md also. OK GO

## Problem 11 - Site testing (app check)

> Moving on to Problem 11: Site testing (app check)
>
> Test the live site and document in output/app_check.html (a page you can click and open). Include clear screenshots and short captions for:
>
> 1. chat checking the inventory level of an item (is it honest stock/price matching the db?)
> 2. the dynamic search-results cards appearing after a category question in the chat
> 3. One of the usability features added in problem 9 (let's show the going fast section)
>
> Make the html easy to grade (a heading for each check, screenshots, one or two sentences on what the screenshot proves). Put the screenshot images in output/app_check_images/ and link them from app_check.html with relative paths (I.e. app_check_images/inventory.png).
>
> OK GO

> Also can you fix: within the product filters it says 2 under long sleeves. There are definitely more than 2 but even worse when you click on it is says there's nothing under long sleeves

> The html needs to be a website that can be opened and screenshots that a human can look at. Needs to be easy for a human to look at and grade.

## Problem 12 - Audit trail, safety, finish harness

> Moving on to Problem 12: Audit trail, safety, finish harness
>
> Keep an append-only output/audit_trail.json of agent-loop activity (time, tool name, shorts args/result, stop reason). DO NOT WIPE IT BETWEEN RUNS. Think of any more safety rules if you can to give the agent and put them in prompts/prompt.md
>
> /harness finish so it's clear how the system works. Model fields in models.py and why you chose them. tools and abilities. safety rules. and specs (loop limits, result caps, models, how to run front + back).
>
> OK GO

## Problem 13 - Push to GitHub and submit the URL

> last problem. Problem 13: Push to Github and submit the URL
>
> push the hw4 code to a public github repository. I will submit this link to canvas for a grade so graders should be able to open it and see. don't put real .env, the campus_customs.db, or product images in the github repo. Use gitignore. Include .env.example with placeholders only.
>
> Follow the layout and other instructions attached
>
> [Image attached: expected file layout — hw4/ with AI_prompts.md, requirements.txt, .env.example, .gitignore, README.md, frontend/ (Vite React TypeScript app), backend/ (main.py, agent.py, models.py, tools.py, prompts/prompt.md), output/ (harness.md, design.md, usability.md, app_check.html, app_check_images/, audit_trail.json); local-only data pack data/ (campus_customs.db, products/) not in git; README.md explains how to run front end and back end after placing the data pack]
