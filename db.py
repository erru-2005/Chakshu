from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import random
import string

load_dotenv()

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.environ.get('DB_NAME', 'chakshu')
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
otp_collection = db['otp_verifications']
mobile_collection = db['student_mobiles']

def generate_otp(length=6):
    """Generate a random OTP"""
    return ''.join(random.choices(string.digits, k=length))

def save_otp(mobile, roll_no, otp):
    """Save OTP to MongoDB with expiration (10 minutes)"""
    expires_at = datetime.now() + timedelta(minutes=10)
    
    # Remove old OTPs for this mobile
    otp_collection.delete_many({
        'mobile': mobile,
        'expires_at': {'$lt': datetime.now()}
    })
    
    # Insert new OTP
    otp_data = {
        'mobile': mobile,
        'roll_no': roll_no,
        'otp': otp,
        'created_at': datetime.now(),
        'expires_at': expires_at,
        'verified': False
    }
    otp_collection.insert_one(otp_data)
    return otp_data

def verify_otp(mobile, roll_no, entered_otp):
    """Verify OTP from MongoDB"""
    otp_record = otp_collection.find_one({
        'mobile': mobile,
        'roll_no': roll_no,
        'otp': entered_otp,
        'verified': False,
        'expires_at': {'$gt': datetime.now()}
    })
    
    if otp_record:
        # Mark OTP as verified
        otp_collection.update_one(
            {'_id': otp_record['_id']},
            {'$set': {'verified': True, 'verified_at': datetime.now()}}
        )
        
        # Save mobile number to collection
        mobile_collection.update_one(
            {'roll_no': roll_no},
            {
                '$set': {
                    'mobile': mobile,
                    'roll_no': roll_no,
                    'verified_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            },
            upsert=True
        )
        
        return True
    return False

def get_student_mobile(roll_no):
    """Get verified mobile number for a student"""
    mobile_record = mobile_collection.find_one({'roll_no': roll_no})
    if mobile_record:
        return mobile_record.get('mobile')
    return None

def cleanup_expired_otps():
    """Clean up expired OTPs"""
    result = otp_collection.delete_many({
        'expires_at': {'$lt': datetime.now()}
    })
    return result.deleted_count

