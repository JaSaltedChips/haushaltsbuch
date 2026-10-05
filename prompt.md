Build a simple, private personal-expense tracking app for my Windows PC.

## Goal

I want to record and understand my German household finances. I will jot transactions in a note on my phone during the day, then manually transfer or paste that log into the app on my PC in the evening. I want useful monthly summaries, charts, and printable reports.

Before coding, inspect the existing workspace and its instructions. Then implement the app in the style of the existing project. If a decision that materially affects the design is unclear, ask me before implementing it. Do not overwrite or discard existing user changes.

## Privacy And Offline Requirements

- The app must work without an internet connection after it has been installed.
- Do not use an LLM, AI service, bank connection, online account, cloud sync, analytics, telemetry, or remote API.
- Do not send financial data off the PC.
- Do not load frontend libraries, fonts, images, or other assets from a CDN. Bundle needed assets locally.
- Run the app locally on the PC and make it accessible only from that PC.
- Store data in a local SQLite database.
- Document installation, offline operation, database location, and backup/export steps.
- The phone log will be transferred manually; do not assume the app can automatically read or sync the phone.

## Technology

Use Python, FastAPI, and SQLite if they fit the existing workspace. Keep the app small and straightforward to operate. Use local frontend assets. Do not add unnecessary AI or cloud dependencies.

## Accounts And Starting Balances

The initial accounts are:
- Four German bank accounts, using user-editable labels such as BANK-1 to BANK-4.
- One German credit card, with a user-editable label such as CARD.
- One cash wallet, labelled CASH.

All initial accounts are in EUR. Do not ask for or store real bank account or card numbers. Let me enter each account’s opening balance and the date that balance applies to. Use 2026-10-04 as the initial tracking start date, but make it configurable.

Represent the credit card as a liability: its balance is the amount owed. A card purchase increases the amount owed. A payment from a bank account to the card reduces both the bank balance and the card amount owed. Make the displayed credit-card balance and reports clear so it cannot be mistaken for money I own.

## Transaction Types And Accounting Rules

Support three main transaction types:

1. Expense: reduces the selected bank or cash balance, or increases the amount owed on CARD if paid by credit card.
2. Income: increases the selected receiving bank account. Include income categories such as salary, interest, and bonus.
3. Transfer: moves money between two of my accounts, with a sender and receiver. Transfers are not income or expenses.

Examples:
- Cash withdrawal: BANK-1 to CASH; not an expense.
- Transfer between banks: BANK-1 to BANK-2; not income or expense.
- Credit-card payment: BANK-1 to CARD; not a second expense.
- Credit-card purchase: an expense assigned to CARD; counts as an expense once.
- Salary: income received into BANK-1.

Store EUR in integer cents internally to avoid floating-point rounding problems. Validate amounts and account references. Provide a way to edit or delete incorrect entries, with confirmation for deletion.

## Phone Log And Evening Entry Workflow

Make daily entry quick. The app must let me paste multiple transactions from my phone note (entries will be ';' separated in the format you deem is good), review how they were interpreted, correct errors, and confirm before saving. Do not silently accept malformed or ambiguous lines. Flag likely duplicates for review but let me decide whether they are duplicates.

Use a documented, simple offline text format. A proposed format is:

DATE | TYPE | AMOUNT | FROM_ACCOUNT | TO_ACCOUNT | CATEGORY | DESCRIPTION

Use `-` for a field that does not apply. Amounts are positive; transaction type determines how the amount affects balances.

Examples:

2026-10-04 | EXPENSE  | 18.70   | CARD    | -      | Eating out | Lunch
2026-10-04 | INCOME   | 3200.00 | -       | BANK-1 | Salary     | October salary
2026-10-04 | TRANSFER | 200.00  | BANK-1  | BANK-2 | -          | Savings
2026-10-04 | TRANSFER | 50.00   | BANK-1  | CASH   | -          | ATM withdrawal

Set the transaction date to today by default when using the manual-entry form. For pasted logs, preserve the date provided on each line. Allow common categories and account labels to be managed in the app.

Suggested expense categories:
Groceries, Eating out, Transport, Housing and bills, Shopping, Health, Travel, Subscriptions, and Other.

Income categories should include at least:
Salary, Interest, Bonus, and Other income.

## Main Screens And Features

Provide these core views:

1. Setup: create and rename accounts, enter opening balances and start date, and manage categories.
2. Daily entry: manually enter one transaction or paste and review a batch of phone-log entries.
3. Transactions: searchable, sortable, filterable table. Allow filtering by date range, transaction type, account, and category. Allow corrections and deletion.
4. Monthly report: select a month and show a readable summary, useful charts, and a detailed transaction table.
5. Backup/export: export transactions and relevant account/category data to CSV. Provide a clear way to back up the SQLite database. Avoid destructive imports.

## Reports And Visualizations

The monthly report should distinguish income, expenses, and transfers. Show:
- Total income by category.
- Total expenses by category.
- Net income minus expenses.
- Recorded ending balance for each bank and cash account.
- Amount owed on the credit card.
- Spending by account or payment method.
- Transfers separately, excluded from income and expense totals.

Include these useful charts:
- Spending by category, preferably a bar chart.
- Spending over time, daily or weekly.
- Income versus expenses for the selected month.
- Optional account or payment-method comparison if it remains clear and readable.

Show the corresponding totals and transaction table; do not make a chart the only way to inspect the data.

Allow printing the report from the browser and saving it as a PDF using the browser’s print-to-PDF feature. Add print styling so charts, totals, and tables are legible and do not split awkwardly across pages.

## Quality And Acceptance Criteria

- The app launches on a Windows PC and remains usable with the internet disconnected.
- No external services, LLM, bank login, or remote assets are required at runtime.
- Database data persists after restarting the app.
- Income, expenses, transfers, cash withdrawals, and credit-card payments update the appropriate balances and report totals correctly.
- Transfers are never counted as income or expenses.
- A credit-card purchase is counted once as an expense; paying the card bill does not count it again.
- Pasted entries can be previewed and corrected before saving.
- Invalid entries are clearly identified and are not silently saved.
- Monthly reports include readable totals, charts, a detailed table, and print/PDF support.
- CSV export and database backup work.
- Add focused tests for the accounting rules, parsing/validation, and report calculations.
- Provide concise instructions for setting up accounts, entering transactions, running the app offline, backing up data, and saving a report as PDF.

Do not commit changes. At completion, summarize the implemented features, files changed, how to run the app, and tests performed.