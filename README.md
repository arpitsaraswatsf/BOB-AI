The Sequential Task Investment Analyst Agent is a Generative AI project developed using IBM Langflow, IBM Orchestrate, and IBM Granite Models.

The agent follows a Sequential Task Execution approach where multiple AI-powered tasks are executed one after another to generate comprehensive investment insights.

Instead of manually researching financial reports, market news, competitor performance, and financial ratios, the system automates the complete workflow and produces an AI-generated investment recommendation.

Note: This project currently runs inside the IBM BOB / IBM watsonx environment and is intended as a proof-of-concept demonstrating the capabilities of IBM's AI orchestration platform.

🚀 Features
Company/Stock Symbol Search
Automated Financial Data Collection
Data Validation & Cleaning
KPI Extraction
Financial Ratio Analysis
Competitor Benchmarking
Market News Analysis
AI-powered Sentiment Analysis
Risk Assessment
Predictive Investment Insights
AI Investment Recommendation
Structured Investment Report
Interactive Dashboard
🏗️ System Workflow
User Input
      │
      ▼
Company Validation
      │
      ▼
Financial Data Collection
      │
      ▼
Data Validation
      │
      ▼
KPI Extraction
      │
      ▼
Financial Ratio Calculation
      │
      ▼
Competitor Analysis
      │
      ▼
Market News Collection
      │
      ▼
Sentiment Analysis
      │
      ▼
Risk Detection
      │
      ▼
Future Prediction
      │
      ▼
Investment Recommendation
      │
      ▼
Dashboard & Report Generation
🧠 Technologies Used
Technology	Purpose
IBM Langflow	Sequential AI workflow
IBM Orchestrate	Workflow automation
IBM Granite Models	AI analysis & recommendations
IBM watsonx	AI Platform
Financial APIs	Market & company data
Dashboard UI	Visualization of results
⚙️ Project Architecture
                User
                  │
                  ▼
        Investment Query
                  │
                  ▼
      IBM Orchestrate Workflow
                  │
                  ▼
         IBM Langflow Pipeline
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
Financial     News API     Company Data
 Data API
      │
      ▼
Data Validation
      │
      ▼
Financial Analysis
      │
      ▼
Sentiment Analysis
      │
      ▼
Risk Detection
      │
      ▼
IBM Granite Model
      │
      ▼
AI Recommendation
      │
      ▼
Dashboard & Report
📊 AI Workflow

The AI agent performs the following sequential tasks:

Step 1

Receive company name or stock ticker.

Step 2

Collect financial information from trusted sources.

Step 3

Validate and clean collected data.

Step 4

Extract important financial KPIs.

Step 5

Calculate financial ratios.

Step 6

Compare company with competitors.

Step 7

Analyze latest financial news.

Step 8

Perform sentiment analysis.

Step 9

Detect potential risks.

Step 10

Generate future growth prediction.

Step 11

Produce AI-powered investment recommendation.

Step 12

Display results in dashboard.

📈 Output

The generated dashboard contains:

Company Overview
Financial KPIs
Financial Ratios
Competitor Comparison
Market News Summary
Sentiment Score
Risk Score
Growth Prediction
Investment Recommendation
Final AI Report
📁 Project Structure
Sequential-Task-Investment-Agent/
│
├── README.md
├── screenshots/
│
├── architecture/
│
├── workflow/
│
├── reports/
│
└── assets/

Since the project is built entirely inside IBM BOB, there are no standalone source-code files in this repository.

▶️ Running the Project
Prerequisites
IBM watsonx Account
IBM BOB Access
IBM Langflow
IBM Orchestrate
IBM Granite Models
Steps
1.

Open IBM BOB.

2.

Import or open the Sequential Task Investment Analyst Agent workflow.

3.

Ensure the required IBM Granite model is selected.

4.

Run the workflow.

5.

Enter a company name or stock symbol (e.g., AAPL, TSLA, MSFT).

6.

Wait for the workflow to execute all sequential tasks.

7.

Review the generated dashboard and investment report.

📸 Screenshots

Add screenshots here.

screenshots/

home.png

workflow.png

dashboard.png

recommendation.png

report.png
📌 Example
Input
AAPL
Output
Company Overview

Revenue

Net Income

PE Ratio

Competitor Comparison

Market Sentiment

Risk Score

Future Prediction

Recommendation

BUY
🌟 Future Improvements
Real-time stock market updates
Portfolio analysis
Personalized investment recommendations
Multi-market support
Cryptocurrency analysis
ESG-based investment scoring
Email report generation
Voice assistant integration
Explainable AI recommendations
Integration with brokerage platforms
⚠️ Limitations
The project currently executes only within the IBM BOB / IBM watsonx environment.
It is not packaged as a standalone web or desktop application.
External users require access to the IBM platform to run the workflow.
Financial outputs depend on the availability and quality of integrated data sources.
🎯 Project Domain

FinTech | Generative AI | Sequential AI Agents | Investment Analysis | Workflow Automation

👨‍💻 Author

Your Name

MCA Student

Generative AI | Python | AI Automation | IBM watsonx

GitHub: Add your GitHub profile here

LinkedIn: Add your LinkedIn profile here

📄 License

This project is developed for educational and demonstration purposes as part of an AI/IBM watsonx implementation. It is not intended to provide real financial or investment advice. Users should conduct their own research and consult qualified financial professionals before making investment decisions.
