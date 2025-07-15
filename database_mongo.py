import pymongo
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import json
from bson import ObjectId

class Database:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.jobs = self.db.jobs
        self.forwarded_messages = self.db.forwarded_messages
        self.user_states = self.db.user_states
        self.users = self.db.users
        self.init_db()

    def init_db(self):
        """Initialize database collections and indexes"""
        # MongoDB creates collections automatically, but we can create indexes
        self.jobs.create_index([("user_id", pymongo.ASCENDING)])
        self.jobs.create_index([("is_active", pymongo.ASCENDING)])
        self.forwarded_messages.create_index([("job_id", pymongo.ASCENDING)])
        self.forwarded_messages.create_index([("forwarded_at", pymongo.ASCENDING)], expireAfterSeconds=60 * 60 * 24 * 7) # Auto-delete after 7 days
        self.users.create_index([("user_id", pymongo.ASCENDING)], unique=True)

    def create_job(self, user_id: int, job_data: dict) -> str:
        """Create a new forwarding job"""
        job_document = {
            "user_id": user_id,
            "job_name": job_data['name'],
            "source_channel_id": job_data['source'],
            "target_channel_id": job_data['target'],
            "start_post_id": job_data['start_id'],
            "end_post_id": job_data['end_id'],
            "batch_size": job_data['batch_size'],
            "recurring_time": job_data['recurring_time'],
            "delete_time": job_data['delete_time'],
            "filter_type": job_data['filter_type'],
            "custom_caption": job_data.get('caption', ''),
            "button_text": job_data.get('button_text', ''),
            "button_url": job_data.get('button_url', ''),
            "is_active": False,
            "last_forwarded_id": 0,
            "created_at": datetime.utcnow().replace(tzinfo=timezone.utc),
            "updated_at": datetime.utcnow().replace(tzinfo=timezone.utc)
        }
        result = self.jobs.insert_one(job_document)
        return str(result.inserted_id)

    def get_user_jobs(self, user_id: int) -> List[dict]:
        """Get all jobs for a user"""
        jobs_cursor = self.jobs.find({"user_id": user_id}).sort("created_at", pymongo.DESCENDING)
        jobs = []
        for job in jobs_cursor:
            job['id'] = str(job['_id'])
            jobs.append(job)
        return jobs

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get a specific job by ID"""
        try:
            job = self.jobs.find_one({"_id": ObjectId(job_id)})
            if job:
                job['id'] = str(job['_id'])
            return job
        except Exception:
            return None

    def update_job_status(self, job_id: str, is_active: bool):
        """Update job active status"""
        self.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"is_active": is_active, "updated_at": datetime.utcnow().replace(tzinfo=timezone.utc)}}
        )

    def update_last_forwarded(self, job_id: str, message_id: int):
        """Update the last forwarded message ID"""
        self.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"last_forwarded_id": message_id, "updated_at": datetime.utcnow().replace(tzinfo=timezone.utc)}}
        )

    def add_forwarded_message(self, job_id: str, original_id: int, forwarded_id: int):
        """Track a forwarded message"""
        self.forwarded_messages.insert_one({
            "job_id": ObjectId(job_id),
            "original_message_id": original_id,
            "forwarded_message_id": forwarded_id,
            "forwarded_at": datetime.utcnow().replace(tzinfo=timezone.utc)
        })

    def get_old_forwarded_messages(self, job_id: str, minutes_ago: int) -> List[int]:
        """Get forwarded messages older than specified minutes"""
        if minutes_ago <= 0:
            return []

        cutoff_time = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=minutes_ago)

        messages_cursor = self.forwarded_messages.find({
            "job_id": ObjectId(job_id),
            "forwarded_at": {"$lt": cutoff_time}
        })

        message_ids = [msg['forwarded_message_id'] for msg in messages_cursor]

        # Clean up old records
        self.forwarded_messages.delete_many({
            "job_id": ObjectId(job_id),
            "forwarded_at": {"$lt": cutoff_time}
        })

        return message_ids

    def save_user_state(self, user_id: int, state_data: dict):
        """Save user's current state"""
        self.user_states.update_one(
            {"user_id": user_id},
            {"$set": {"state_data": json.dumps(state_data), "updated_at": datetime.utcnow().replace(tzinfo=timezone.utc)}},
            upsert=True
        )

    def get_user_state(self, user_id: int) -> Optional[dict]:
        """Get user's current state"""
        state = self.user_states.find_one({"user_id": user_id})
        if state:
            return json.loads(state['state_data'])
        return None

    def clear_user_state(self, user_id: int):
        """Clear user's state"""
        self.user_states.delete_one({"user_id": user_id})

    def reset_job_progress(self, job_id: str, start_post_id: int):
        """Reset the last forwarded message ID for a job"""
        self.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"last_forwarded_id": start_post_id - 1, "updated_at": datetime.utcnow().replace(tzinfo=timezone.utc)}}
        )
        self.forwarded_messages.delete_many({"job_id": ObjectId(job_id)})

    def delete_job(self, job_id: str):
        """Delete a job by its ID"""
        self.jobs.delete_one({"_id": ObjectId(job_id)})
        self.forwarded_messages.delete_many({"job_id": ObjectId(job_id)})

    def update_job(self, job_id: str, update_data: dict):
        """Update a job with new data"""
        update_data['updated_at'] = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )

    def add_user_if_not_exists(self, user_id: int):
        """Add a user to the users table if they don't already exist."""
        self.users.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {"first_interaction_at": datetime.utcnow().replace(tzinfo=timezone.utc)}},
            upsert=True
        )

    def get_total_users(self) -> int:
        """Get the total count of unique users who have interacted with the bot."""
        return self.users.count_documents({})

    def get_total_jobs(self) -> int:
        """Get the total count of all jobs created."""
        return self.jobs.count_documents({})

    def get_total_forwarded_messages(self) -> int:
        """Get the total count of all messages ever forwarded."""
        return self.forwarded_messages.count_documents({})

    def get_jobs_created_today(self) -> int:
        """Get the count of jobs created today (UTC)."""
        today_start_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        return self.jobs.count_documents({"created_at": {"$gte": today_start_utc}})

    def get_forwarded_messages_today(self) -> int:
        """Get the count of messages forwarded today (UTC)."""
        today_start_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        return self.forwarded_messages.count_documents({"forwarded_at": {"$gte": today_start_utc}})
