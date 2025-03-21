# **Facebook Group Sentiment Analysis Project**  

## **Overview**  
This project collects data from a **Facebook group** and performs **sentiment analysis** on posts. The data is stored in a **MySQL database** and displayed on a **dashboard** for analysis.  

## **System Diagram**  
- 📌 **System Overview** → 
![System Diagram](https://github.com/sirinapa-git/Scrape_LLM/blob/main/facebookgroup/conf/png/sys.png)
- 📌 **Database Structure & Final Data** → 
![Database](https://github.com/sirinapa-git/Scrape_LLM/blob/main/facebookgroup/conf/png/database.png)

## **Project Workflow**  

### **1. Data Collection (Scraping Facebook Group)**  
- **Runs at:** `06:00 AM` and `06:00 PM`  
- Scrapes posts from the **Facebook group** and stores them in the database.  

### **2. Sentiment Analysis (Model Processing)**  
- **Runs after scraping data**  
- The **model processes new posts** and classifies sentiment as **Positive, Neutral, or Negative**.  
- ✅ **Handles duplicate posts:**  
  - If a post is **already in the database**, only **reactions are updated**.  

### **3. Daily Configuration (`config_daily`)**  
- **Runs after sentiment model processing**  
- Extracts data into **two summary tables**:  
  - **`daily_summary`** → (Tag + Sentiment Count)  
  - **`tag_summary`** → (Tag Count Summary)  

### **4. Post Cleanup (`config_del`)**  
- **Runs at:** `01:00 AM`  
- **Deletes yesterday's posts** and keeps only **Top 5 sentiment posts**.  
- 🚀 **All other posts are deleted except the Top 5**.  

## **Installation & Setup**  
### **1. Install Dependencies**  
```sh  
pip install -r requirements.txt  
```  

### **2. Set Up the Database**  
- Create a **MySQL database** and update **database credentials** in `config.py`.  

### **3. Run the System**  
```sh  
python main.py  
```  