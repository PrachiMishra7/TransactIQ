import os
import random
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from config import settings
from services.processor import process_upload
from models import Upload, ProcessingStatus

def generate_realistic_dataset(num_rows: int = 5000) -> pd.DataFrame:
    """Generates a highly realistic, rich e-commerce dataset with intentional data quality issues."""
    
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "company.org", "test.com", "mailinator.com", "tempmail.net"]
    countries = ["India", "Singapore", "United States", "United Kingdom", "Australia"]
    products = [
        ("Wireless Noise-Canceling Headphones", 299.99),
        ("Ergonomic Office Chair", 199.50),
        ("4K Ultra HD Smart TV", 799.00),
        ("Mechanical Gaming Keyboard", 129.99),
        ("Bluetooth Smartwatch", 249.00),
        ("Stainless Steel Water Bottle", 24.99),
        ("USB-C Fast Charger", 19.99),
        ("Home Security Camera", 149.95),
        ("Yoga Mat Extra Thick", 34.50),
        ("Professional Blender", 119.00)
    ]
    
    data = []
    base_date = datetime.now() - timedelta(days=180)
    
    for i in range(num_rows):
        # Good Data Baseline
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        name = f"{fname} {lname}"
        country = random.choices(countries, weights=[40, 20, 20, 10, 10])[0]
        
        if country == "India":
            phone = f"+91 {random.randint(6000000000, 9999999999)}"
        elif country == "Singapore":
            phone = f"+65 {random.randint(80000000, 99999999)}"
        else:
            phone = f"+1 {random.randint(2000000000, 9999999999)}"
            
        email = f"{fname.lower()}.{lname.lower()}{random.randint(1,99)}@{random.choice(domains)}"
        
        prod, price = random.choice(products)
        qty = random.randint(1, 5)
        
        order_date = base_date + timedelta(days=random.randint(0, 170), hours=random.randint(0, 23))
        delivery_date = order_date + timedelta(days=random.randint(1, 10))
        
        txn_id = f"TXN-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}"
        payment_method = random.choices(["credit_card", "paypal", "bank_transfer", "cash"], weights=[60, 20, 15, 5])[0]
        
        row = {
            "order_id": f"ORD-{random.randint(10000, 99999)}",
            "customer_name": name,
            "email": email,
            "phone": phone,
            "country": country,
            "product_name": prod,
            "sku": f"SKU-{random.randint(100, 999)}",
            "quantity": qty,
            "unit_price": price,
            "total_price": round(qty * price, 2),
            "payment_method": payment_method,
            "transaction_id": txn_id,
            "order_date": order_date.strftime("%Y-%m-%d"),
            "delivery_date": delivery_date.strftime("%Y-%m-%d"),
        }
        
        # Inject realistic data quality errors randomly!
        err_prob = random.random()
        
        if err_prob < 0.05:
            # Missing critical values
            if random.random() < 0.5:
                row["customer_name"] = None
            else:
                row["order_id"] = ""
                
        elif err_prob < 0.10:
            # Calculation errors (total_price doesn't match qty * unit_price)
            row["total_price"] = round(row["total_price"] * random.uniform(1.1, 1.5), 2)
            
        elif err_prob < 0.15:
            # Relationship errors (delivery before order)
            temp = row["order_date"]
            row["order_date"] = row["delivery_date"]
            row["delivery_date"] = temp
            
        elif err_prob < 0.22:
            # Formatting/Invalid characters in Phone
            row["phone"] = row["phone"].replace("+", "") + " ext 123"
            
        elif err_prob < 0.26:
            # Bad email formatting
            row["email"] = row["email"].replace("@", " at ")
            
        elif err_prob < 0.30:
            # Disposable/Temporary email
            row["email"] = f"spammer123@mailinator.com"
            
        elif err_prob < 0.33 and i > 10:
            # Duplicate Transaction IDs
            row["transaction_id"] = data[i-5]["transaction_id"]
            
        data.append(row)
        
    return pd.DataFrame(data)

async def seed_demo_data(db: Session):
    print("Seeding initial demo dataset for deployment...")
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # 1. Create a highly imperfect 5,000 row dataset
    df = generate_realistic_dataset(5000)
    file_path = os.path.join(settings.upload_dir, "xeno_global_demo_dataset.csv")
    df.to_csv(file_path, index=False)
    
    file_size = os.path.getsize(file_path)
    
    # 2. Register Upload in DB
    new_upload = Upload(
        file_name="xeno_global_demo_dataset.csv",
        file_size=file_size,
        total_rows=len(df),
        processing_status=ProcessingStatus.PENDING,
        validation_settings={"phone": True, "date": True, "duplicate": True, "payment": True}
    )
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)
    
    # 3. Process it synchronously so it's ready immediately
    try:
        await process_upload(db, new_upload.id, file_path, user_mapping=None, validation_settings=new_upload.validation_settings)
        print("Demo dataset seeded successfully!")
    except Exception as e:
        print(f"Failed to seed demo data: {e}")
