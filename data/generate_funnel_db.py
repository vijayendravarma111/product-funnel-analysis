import sqlite3
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_data(num_users=10000, seed=42):
    np.random.seed(seed)
    
    # User demographics / attributes
    groups = ['Control A', 'Variant B']
    devices = ['Mobile', 'Desktop', 'Tablet']
    sources = ['Organic', 'Paid Search', 'Social Media', 'Email', 'Referral']
    
    device_weights = [0.60, 0.30, 0.10]
    source_weights = [0.30, 0.25, 0.20, 0.15, 0.10]
    
    # Probability parameters for funnel transitions
    # Control A transitions: View -> Cart -> Checkout -> Purchase
    p_cart_a, p_checkout_a, p_purchase_a = 0.30, 0.40, 0.50
    # Variant B transitions: View -> Cart -> Checkout -> Purchase (higher conversion rates)
    p_cart_b, p_checkout_b, p_purchase_b = 0.35, 0.48, 0.60
    
    # Base timestamp range: 2026-05-01 to 2026-05-30
    start_date = datetime(2026, 5, 1)
    
    events_list = []
    
    for i in range(1, num_users + 1):
        user_id = f"U{i:06d}"
        ab_group = np.random.choice(groups)
        device = np.random.choice(devices, p=device_weights)
        traffic_source = np.random.choice(sources, p=source_weights)
        
        # User starting time (view event)
        start_offset_seconds = np.random.randint(0, 30 * 24 * 3600)
        t_view = start_date + timedelta(seconds=start_offset_seconds)
        
        # Base probabilities depending on group
        if ab_group == 'Control A':
            p_cart, p_checkout, p_purchase = p_cart_a, p_checkout_a, p_purchase_a
        else:
            p_cart, p_checkout, p_purchase = p_cart_b, p_checkout_b, p_purchase_b
            
        # Add modifier based on device
        if device == 'Desktop':
            modifier = 0.05
        elif device == 'Tablet':
            modifier = 0.00
        else: # Mobile
            modifier = -0.03
            
        # Add modifier based on traffic source
        if traffic_source in ['Organic', 'Email']:
            modifier += 0.03
        elif traffic_source == 'Social Media':
            modifier -= 0.05
            
        # Apply modifiers and clamp to [0.01, 0.99]
        p_cart = np.clip(p_cart + modifier, 0.01, 0.99)
        p_checkout = np.clip(p_checkout + modifier, 0.01, 0.99)
        p_purchase = np.clip(p_purchase + modifier, 0.01, 0.99)
        
        # 1. View Event (all users get this)
        events_list.append({
            'user_id': user_id,
            'timestamp': t_view.strftime('%Y-%m-%d %H:%M:%S'),
            'event_type': 'view',
            'device': device,
            'traffic_source': traffic_source,
            'ab_group': ab_group
        })
        
        # 2. Cart Event
        if np.random.random() < p_cart:
            # Time delay view -> cart: exponential distribution (mean = 10 minutes = 0.16 hours)
            delay_cart = np.random.exponential(scale=0.16) # hours
            t_cart = t_view + timedelta(seconds=int(delay_cart * 3600))
            events_list.append({
                'user_id': user_id,
                'timestamp': t_cart.strftime('%Y-%m-%d %H:%M:%S'),
                'event_type': 'cart',
                'device': device,
                'traffic_source': traffic_source,
                'ab_group': ab_group
            })
            
            # 3. Checkout Event
            if np.random.random() < p_checkout:
                # Time delay cart -> checkout: exponential distribution (mean = 5 minutes = 0.08 hours)
                delay_checkout = np.random.exponential(scale=0.08) # hours
                t_checkout = t_cart + timedelta(seconds=int(delay_checkout * 3600))
                events_list.append({
                    'user_id': user_id,
                    'timestamp': t_checkout.strftime('%Y-%m-%d %H:%M:%S'),
                    'event_type': 'checkout',
                    'device': device,
                    'traffic_source': traffic_source,
                    'ab_group': ab_group
                })
                
                # 4. Purchase Event
                if np.random.random() < p_purchase:
                    # Time delay checkout -> purchase:
                    # Control A has mean = 15 mins (0.25 hours), Variant B has mean = 5 mins (0.08 hours)
                    scale_purchase = 0.25 if ab_group == 'Control A' else 0.08
                    delay_purchase = np.random.exponential(scale=scale_purchase) # hours
                    t_purchase = t_checkout + timedelta(seconds=int(delay_purchase * 3600))
                    events_list.append({
                        'user_id': user_id,
                        'timestamp': t_purchase.strftime('%Y-%m-%d %H:%M:%S'),
                        'event_type': 'purchase',
                        'device': device,
                        'traffic_source': traffic_source,
                        'ab_group': ab_group
                    })
                    
    df = pd.DataFrame(events_list)
    # Sort events chronologically to simulate a real event stream
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['timestamp', 'user_id']).reset_index(drop=True)
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return df

def save_to_sqlite(df, db_path='data/events.db'):
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing table if exists
    cursor.execute("DROP TABLE IF EXISTS events")
    
    # Create table schema
    cursor.execute("""
    CREATE TABLE events (
        user_id TEXT,
        timestamp TEXT,
        event_type TEXT,
        device TEXT,
        traffic_source TEXT,
        ab_group TEXT
    )
    """)
    
    # Insert dataframe records into SQLite
    df.to_sql('events', conn, if_exists='append', index=False)
    
    # Create index on user_id and timestamp for query optimization
    cursor.execute("CREATE INDEX idx_user_timestamp ON events(user_id, timestamp)")
    cursor.execute("CREATE INDEX idx_event_type ON events(event_type)")
    cursor.execute("CREATE INDEX idx_ab_group ON events(ab_group)")
    
    conn.commit()
    conn.close()
    print(f"Successfully generated database at {db_path} with {len(df)} events.")

if __name__ == "__main__":
    df = generate_data(num_users=10000)
    save_to_sqlite(df)
    
    # Print basic summary
    print("\nEvent type counts:")
    print(df['event_type'].value_counts())
    
    print("\nConversion rate comparison (view to purchase):")
    funnel = df.groupby(['user_id', 'ab_group'])['event_type'].apply(list).reset_index()
    funnel['converted'] = funnel['event_type'].apply(lambda x: 'purchase' in x)
    summary = funnel.groupby('ab_group')['converted'].agg(['count', 'sum', 'mean'])
    summary.columns = ['Total Users', 'Purchased Users', 'Conversion Rate']
    summary['Conversion Rate'] = (summary['Conversion Rate'] * 100).round(2).astype(str) + '%'
    print(summary)
