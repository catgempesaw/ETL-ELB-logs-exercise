# ETL Exercise: ELB Log Essentials to MySQL

## 📌 Objective

This exercise demonstrates how to extract AWS Application Load Balancer (ALB) access logs from an S3 bucket, transform key log data, and load the processed results into a MySQL database table.

---

## ⚙️ Technology Stack

- **Python** – scripting the ETL process  
- **boto3** – access and download logs from AWS S3  
- **pandas** – for optional data manipulation  
- **SQLAlchemy** – connect and insert into MySQL  
- **AWS S3** – source of gzipped ELB access logs  
- **MySQL** – target database for the transformed data

---

## 📥 Input: ELB Access Logs

- **Source**: AWS S3 bucket
- **Format**: ALB access logs, space-delimited  
- **Compression**: May be `.gz` compressed files

## 🔄 ETL Workflow

### ✅ Extraction
- Connect to S3 using `boto3`
- List and download `.gz` log files from the specified prefix
- Read and decode each line

### ✅ Transformation
For each log entry:
- Parse standard ALB fields (quoted and unquoted)
- Extract and convert

### ✅ Loading
- Insert transformed rows into the table in MySQL using SQLAlchemy
