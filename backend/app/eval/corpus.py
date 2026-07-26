EVAL_FILENAME = "meridian_industries_annual_report_fy2024.pdf"

PAGES: list[tuple[int, str]] = [
    (
        1,
        "Meridian Industries Limited — Annual Report FY2024. "
        "Meridian Industries is a diversified Indian manufacturer operating across three segments: "
        "industrial automation, specialty chemicals, and renewable energy components. "
        "The company is headquartered in Pune, Maharashtra, and is listed on the NSE and BSE. "
        "In the financial year ended 31 March 2024, consolidated revenue from operations grew to "
        "18,450 crore rupees, up 14 percent from 16,180 crore in FY2023. "
        "Reported EBITDA for FY2024 was 3,120 crore, giving an EBITDA margin of 16.9 percent, "
        "an improvement of 90 basis points over the prior year. "
        "Profit after tax attributable to shareholders rose to 1,742 crore, from 1,405 crore in FY2023."
    ),
    (
        2,
        "Balance sheet and capital structure. "
        "As of 31 March 2024, total debt stood at 4,050 crore against shareholders equity of 13,500 crore, "
        "resulting in a debt to equity ratio of 0.30. "
        "Net debt to EBITDA was 1.1 times. "
        "Cash and cash equivalents at year end were 2,600 crore. "
        "Return on equity for FY2024 was 12.9 percent and return on capital employed was 15.4 percent. "
        "The board recommended a final dividend of 8 rupees per share, taking the total dividend for the year to "
        "12 rupees per share, a payout ratio of approximately 28 percent."
    ),
    (
        3,
        "Segment performance. "
        "The industrial automation segment contributed 7,900 crore of revenue, growing 11 percent, "
        "with a segment margin of 18 percent. "
        "Specialty chemicals contributed 6,300 crore, growing 9 percent, but margins compressed to 14 percent "
        "due to higher raw material and energy costs. "
        "The renewable energy components segment was the fastest growing at 32 percent, reaching 4,250 crore, "
        "driven by strong demand for solar inverters and battery management systems. "
        "Management expects the renewable segment to cross 6,000 crore of revenue by FY2026."
    ),
    (
        4,
        "Risk factors and outlook. "
        "Key risks disclosed by management include: foreign exchange exposure, as roughly 40 percent of raw "
        "materials are imported and priced in US dollars; customer concentration, with the top five customers "
        "accounting for 27 percent of revenue; and regulatory risk in the specialty chemicals segment relating "
        "to environmental compliance. "
        "The company faced a working capital increase during the year as inventory days rose from 58 to 66. "
        "For FY2025, management has guided to revenue growth of 12 to 15 percent and targets an EBITDA margin "
        "of 17 to 18 percent, supported by operating leverage in the renewable segment and cost optimisation in chemicals."
    ),
    (
        5,
        "Capital expenditure and sustainability. "
        "Capital expenditure for FY2024 was 1,850 crore, primarily directed towards a new solar inverter plant "
        "in Gujarat and capacity expansion in specialty chemicals. "
        "The company has committed to sourcing 60 percent of its electricity from renewable sources by FY2027 "
        "and achieving carbon neutrality in its own operations by FY2035. "
        "Research and development spending was 520 crore, or 2.8 percent of revenue, focused on next generation "
        "battery management systems and low emission chemical processes. "
        "The workforce stood at 14,200 employees at year end, with attrition of 11 percent."
    ),
]

QUESTIONS: list[str] = [
    "What was Meridian Industries' consolidated revenue in FY2024 and how much did it grow?",
    "What was the debt to equity ratio and net debt to EBITDA at the end of FY2024?",
    "Which business segment grew the fastest and what drove that growth?",
    "What dividend did the board recommend for FY2024 and what was the payout ratio?",
    "What are the key risk factors disclosed by management?",
    "What is management's revenue growth and EBITDA margin guidance for FY2025?",
    "How much did the company spend on capital expenditure and research and development in FY2024?",
]
